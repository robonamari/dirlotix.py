import datetime
import mimetypes
import os
import zoneinfo
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, send_file
from flask_compress import Compress
from werkzeug.wrappers import Response

from utils.i18n import get_translator

load_dotenv(".env")

app = Flask(__name__, static_folder="assets")
app.add_url_rule("/favicon.ico", endpoint="favicon", redirect_to=os.getenv("FAVICON"))
app.add_url_rule(
    "/",
    endpoint="root_redirect",
    view_func=lambda: redirect(
        "/en" + (f"?{request.query_string.decode()}" if request.query_string else "")
    ),
)
Compress(app)


@app.get("/<language_code>")
async def index(language_code: str) -> Response:
    """
    Render directory listing page for the given language.

    Validates the language, loads translation, lists directory contents, and renders page.

    Args:
        lang_code (str): Two-letter language code.

    Returns:
        Any: Rendered HTML or error response.
    """
    available_languages = {
        d.name
        for d in Path("languages").iterdir()
        if d.is_dir() and (d / "LC_MESSAGES" / "messages.mo").exists()
    }
    if language_code not in available_languages:
        return await download_file(language_code)
    root_directory = os.path.join(os.path.dirname(__file__), "downloads")
    current_directory = os.path.normpath(
        os.path.join(root_directory, request.args.get("dir", ""))
    )
    if not current_directory.startswith(root_directory) or not os.path.isdir(
        current_directory
    ):
        return abort(404)
    _ = get_translator(language_code).gettext
    items = []
    if current_directory != root_directory:
        parent_directory = os.path.dirname(current_directory)
        link = (
            f"/{language_code}"
            if parent_directory == root_directory
            else f"/{language_code}?dir={os.path.relpath(parent_directory, root_directory)}"
        )
        items.append(
            {
                "icon": "fas fa-level-up-alt",
                "name": _("Previous Folder"),
                "link": link,
            }
        )
    ignored_files = set(os.getenv("IGNORE_FILES", "").split(","))
    for entry_name in sorted(
        f
        for f in os.listdir(current_directory)
        if not f.startswith(".") and f not in ignored_files
    ):
        entry_path = os.path.join(current_directory, entry_name)
        if os.path.isfile(entry_path):
            mime_type, _ = mimetypes.guess_type(entry_path)
            mime_main_type = mime_type.split("/")[0] if mime_type else ""
            mime_icon_map = {
                "video": "fas fa-video",
                "image": "fas fa-image",
                "audio": "fas fa-music",
                "application/pdf": "fas fa-file-pdf",
                "application/msword": "fas fa-file-word",
                "application/vnd.ms-excel": "fas fa-file-excel",
                "application/vnd.ms-powerpoint": "fas fa-file-powerpoint",
                "application/zip": "fas fa-file-archive",
                "application/x-rar-compressed": "fas fa-file-archive",
                "text/html": "fab fa-html5",
                "text/css": "fab fa-css3",
                "application/json": "fas fa-file-code",
                "application/javascript": "fab fa-js",
                "text/plain": "fas fa-file-alt",
            }
            icon = mime_icon_map.get(
                mime_type or "", mime_icon_map.get(mime_main_type, "fas fa-file")
            )
            file_size_bytes = os.path.getsize(entry_path)
            size_index = min(4, max(0, (file_size_bytes.bit_length() - 1) // 10))
            size_unit_labels = ["B", "KB", "MB", "GB", "TB"]
            file_size = file_size_bytes / (1024**size_index)
            items.append(
                {
                    "icon": icon,
                    "name": entry_name,
                    "link": f"/{quote(os.path.relpath(entry_path, root_directory))}",
                    "size": f"{file_size:.2f}{size_unit_labels[size_index]}",
                    "date": datetime.datetime.fromtimestamp(
                        os.path.getmtime(entry_path), zoneinfo.ZoneInfo("UTC")
                    ).isoformat(timespec="seconds"),
                }
            )
        else:
            items.append(
                {
                    "icon": "fas fa-folder-open",
                    "name": entry_name,
                    "link": f"/{language_code}?dir={quote(os.path.relpath(entry_path, root_directory))}",
                }
            )
    return Response(
        render_template(
            "index.min.html",
            file_list=items,
            lang=language_code,
            _=get_translator(language_code).gettext,
            font_family=os.getenv("FONT_FAMILY"),
            favicon=os.getenv("FAVICON"),
            theme_color=os.getenv("THEME_COLOR"),
        ),
        mimetype="text/html",
    )


@app.get("/LICENSE")
async def show_license() -> Response:
    """
    Serve the LICENSE file as plain text.

    Returns:
        Response: Flask response containing the content of the LICENSE file with 'text/plain' MIME type.

    Raises:
        404: If the LICENSE file is not found.
    """
    return send_file("LICENSE", mimetype="text/plain")


@app.get("/<path:requested_filename>")
async def download_file(requested_filename: str) -> Response:
    """
    Serve a file securely for download or inline display based on MIME type.

    Args:
        filename (str): Relative file path requested.

    Returns:
        Response: Flask response serving the file or aborts if access denied.
    """
    root_directory = Path(
        os.path.join(os.path.dirname(__file__), "downloads")
    ).resolve()
    entry_path = (root_directory / requested_filename).resolve()
    if not str(entry_path).startswith(str(root_directory)):
        return abort(403)
    if not entry_path.is_file():
        return abort(404)
    return send_file(str(entry_path), as_attachment=True, conditional=True)


@app.errorhandler(Exception)
async def handle_error(exception: Exception) -> Response:
    """
    Handle exceptions and render appropriate error pages based on error code.

    Args:
        error (Exception): The exception that occurred.

    Returns:
        Response: Flask response with rendered error page and appropriate status code.
    """
    status_code: int = getattr(exception, "code", 500)
    match status_code:
        case 400 | 401 | 403 | 404 | 500 | 503:
            template_name = str(status_code)
        case _:
            template_name = "500"
    return Response(
        render_template(f"errors/{template_name}.html"),
        status=status_code,
        mimetype="text/html",
    )


if __name__ == "__main__":
    app.run(debug=True)

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


@app.get("/<lang_code>")
async def index(lang_code: str) -> Response:
    """
    Render directory listing page for the given language.

    Validates the language, loads translation, lists directory contents, and renders page.

    Args:
        lang_code (str): Two-letter language code.

    Returns:
        Any: Rendered HTML or error response.
    """
    valid_languages = {
        d.name
        for d in Path("languages").iterdir()
        if d.is_dir() and (d / "LC_MESSAGES" / "messages.mo").exists()
    }
    if lang_code not in valid_languages:
        return await download_file(lang_code)
    safe_root = os.path.join(os.path.dirname(__file__), "downloads")
    directory = os.path.normpath(os.path.join(safe_root, request.args.get("dir", "")))
    if not directory.startswith(safe_root) or not os.path.isdir(directory):
        return abort(404)
    _ = get_translator(lang_code).gettext
    file_list = []
    if directory != safe_root:
        parent_dir = os.path.dirname(directory)
        link = (
            f"/{lang_code}"
            if parent_dir == safe_root
            else f"/{lang_code}?dir={os.path.relpath(parent_dir, safe_root)}"
        )
        file_list.append(
            {
                "icon": "fas fa-level-up-alt",
                "name": _("Previous Folder"),
                "link": link,
            }
        )
    ignore_files = set(os.getenv("IGNORE_FILES", "").split(","))
    for name in sorted(
        f
        for f in os.listdir(directory)
        if not f.startswith(".") and f not in ignore_files
    ):
        file_path = os.path.join(directory, name)
        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            main_type = mime_type.split("/")[0] if mime_type else ""
            icon_map = {
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
            icon = icon_map.get(mime_type or "", icon_map.get(main_type, "fas fa-file"))
            size_bytes = os.path.getsize(file_path)
            idx = min(4, max(0, (size_bytes.bit_length() - 1) // 10))
            size_units = ["B", "KB", "MB", "GB", "TB"]
            size = size_bytes / (1024**idx)
            file_list.append(
                {
                    "icon": icon,
                    "name": name,
                    "link": f"/{quote(os.path.relpath(file_path, safe_root))}",
                    "size": f"{size:.2f}{size_units[idx]}",
                    "date": datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path), zoneinfo.ZoneInfo("UTC")
                    ).isoformat(timespec="seconds"),
                }
            )
        else:
            file_list.append(
                {
                    "icon": "fas fa-folder-open",
                    "name": name,
                    "link": f"/{lang_code}?dir={quote(os.path.relpath(file_path, safe_root))}",
                }
            )
    return Response(
        render_template(
            "index.min.html",
            file_list=file_list,
            lang=lang_code,
            _=get_translator(lang_code).gettext,
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


@app.get("/<path:filename>")
async def download_file(filename: str) -> Response:
    """
    Serve a file securely for download or inline display based on MIME type.

    Args:
        filename (str): Relative file path requested.

    Returns:
        Response: Flask response serving the file or aborts if access denied.
    """
    safe_root: str = os.path.join(os.path.dirname(__file__), "downloads")
    file_path: str = os.path.normpath(os.path.join(safe_root, filename))
    if os.path.isfile(file_path):
        if not file_path.startswith(safe_root):
            return abort(403)
        ignore_files = set(os.getenv("IGNORE_FILES", "").split(","))
        for part in filename.split("/"):
            if part in ignore_files:
                return abort(403)
        return send_file(file_path, as_attachment=True)
    return abort(404)


@app.errorhandler(Exception)
async def handle_error(error: Exception) -> Response:
    """
    Handle exceptions and render appropriate error pages based on error code.

    Args:
        error (Exception): The exception that occurred.

    Returns:
        Response: Flask response with rendered error page and appropriate status code.
    """
    error_code: int = getattr(error, "code", 500)
    match error_code:
        case 400 | 401 | 403 | 404 | 500 | 503:
            error_page = str(error_code)
        case _:
            error_page = "500"
    return Response(
        render_template(f"errors/{error_page}.html"),
        status=error_code,
        mimetype="text/html",
    )


if __name__ == "__main__":
    app.run(debug=True)

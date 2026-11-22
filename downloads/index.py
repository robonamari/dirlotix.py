import mimetypes
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import minify_html
from dotenv import load_dotenv
from flask import Flask, Response, abort, redirect, render_template, request, send_file
from flask_compress import Compress
from werkzeug.exceptions import HTTPException

from utils.i18n import get_translator

load_dotenv(".env")

app: Flask = Flask(__name__, static_folder="assets")
app.add_url_rule("/favicon.ico", endpoint="favicon", redirect_to=os.getenv("FAVICON"))
app.add_url_rule(
    "/",
    endpoint="root_redirect",
    view_func=lambda: redirect(
        "/en" + (f"?{request.query_string.decode()}" if request.query_string else ""),
    ),
)
Compress(app)

MIME_ICON_MAP: dict[str, str] = {
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
SIZE_UNITS: list[str] = ["B", "KB", "MB", "GB", "TB"]


@app.get("/<language_code>")
def index(language_code: str) -> Response:
    """Display the downloads directory with localized navigation.

    Args:
        language_code (str): The language code for the interface.

    Returns:
        Response: The rendered file browser page or a file download response.

    """
    available_languages: set[str] = {
        d.name
        for d in Path("languages").iterdir()
        if d.is_dir() and (d / "LC_MESSAGES" / "messages.mo").exists()
    }
    if language_code not in available_languages:
        return download_file(language_code)
    root_directory: Path = (Path(__file__).parent / "downloads").resolve()
    current_directory: Path = (root_directory / request.args.get("dir", "")).resolve()
    try:
        current_directory.relative_to(root_directory)
    except ValueError:
        abort(404)
    if not current_directory.is_dir():
        abort(404)
    translator = get_translator(language_code)
    items: list[dict[str, Any]] = []
    if current_directory != root_directory:
        parent_directory: Path = current_directory.parent
        link: str = (
            f"/{language_code}"
            if parent_directory == root_directory
            else (
                f"/{language_code}?dir="
                f"{quote(str(parent_directory.relative_to(root_directory)))}"
            )
        )
        items.append(
            {
                "icon": "fas fa-level-up-alt",
                "name": translator.gettext("Previous Folder"),
                "link": link,
            },
        )
    ignored_files: set[str] = set(os.getenv("IGNORE_FILES", "").split(","))
    entries: list[Path] = [
        entry
        for entry in current_directory.iterdir()
        if not entry.name.startswith(".") and entry.name not in ignored_files
    ]
    entries.sort(key=lambda entry: (entry.is_file(), entry.name.lower()))
    for entry_path in entries:
        file_stat = entry_path.stat()
        if entry_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(entry_path))
            mime_main_type = mime_type.split("/")[0] if mime_type else ""
            icon: str = MIME_ICON_MAP.get(
                mime_type or "",
                MIME_ICON_MAP.get(mime_main_type, "fas fa-file"),
            )
            file_size_bytes = file_stat.st_size
            size_index: int = min(4, max(0, (file_size_bytes.bit_length() - 1) // 10))
            file_size: float = file_size_bytes / (1024**size_index)
            items.append(
                {
                    "icon": icon,
                    "name": entry_path.name,
                    "link": f"/{quote(str(entry_path.relative_to(root_directory)))}",
                    "size": f"{file_size:.2f}{SIZE_UNITS[size_index]}",
                    "date": datetime.fromtimestamp(file_stat.st_mtime, UTC).isoformat(
                        timespec="seconds",
                    ),
                },
            )
        else:
            items.append(
                {
                    "icon": "fas fa-folder-open",
                    "name": entry_path.name,
                    "link": (
                        f"/{language_code}?dir="
                        f"{quote(str(entry_path.relative_to(root_directory)))}"
                    ),
                },
            )
    return Response(
        render_template(
            "index.html",
            file_list=items,
            lang=language_code,
            _=translator.gettext,
            font_family=os.getenv("FONT_FAMILY"),
            favicon=os.getenv("FAVICON"),
            theme_color=os.getenv("THEME_COLOR"),
        ),
        mimetype="text/html",
    )


@app.get("/LICENSE")
def show_license() -> Response:
    """Serve the LICENSE file as plain text.

    Returns:
        Response: The LICENSE file as a plain-text response.

    """
    return send_file("LICENSE", mimetype="text/plain")


@app.get("/<path:requested_filename>")
def download_file(requested_filename: str) -> Response:
    """Serve a requested file from the downloads directory.

    Args:
        requested_filename (str): The name of the file to download.

    Returns:
        Response: The requested file as a downloadable response.

    """
    root_directory: Path = (Path(__file__).parent / "downloads").resolve()
    entry_path: Path = (root_directory / requested_filename).resolve()
    try:
        entry_path.relative_to(root_directory)
    except ValueError:
        abort(403)
    if not entry_path.is_file():
        abort(404)
    return send_file(str(entry_path), as_attachment=True, conditional=True)


@app.errorhandler(HTTPException)
def handle_error(exception: HTTPException) -> Response:
    """Handle HTTP exceptions and render the appropriate error page.

    Args:
        exception (HTTPException): The HTTP exception that was raised.

    Returns:
        Response: The rendered error page with the corresponding status code.

    """
    status_code: int = getattr(exception, "code", 500)
    template_name: str = (
        str(status_code) if status_code in {400, 401, 403, 404, 500, 503} else "500"
    )
    return Response(
        render_template(f"errors/{template_name}.html"),
        status=status_code,
        mimetype="text/html",
    )


@app.after_request
def minify_html_response(response: Response) -> Response:
    """Minify HTML responses before sending them to the client.

    Args:
        response (Response): The Flask response to process.

    Returns:
        Response: The minified HTML response or the original response.

    """
    if response.mimetype == "text/html" and not response.direct_passthrough:
        response.set_data(
            minify_html.minify(
                response.get_data(as_text=True),
                keep_comments=False,
                minify_css=True,
                minify_js=True,
            ),
        )
    return response


if __name__ == "__main__":
    app.run(debug=True)

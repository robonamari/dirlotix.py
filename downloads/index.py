import datetime
import mimetypes
import os
import zoneinfo
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
        "/en" + (f"?{request.query_string.decode()}" if request.query_string else "")
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
UTC = zoneinfo.ZoneInfo("UTC")


@app.get("/<language_code>")
def index(language_code: str) -> Response:
    """
    Display the contents of the downloads directory in a web interface, allowing users to navigate through folders and download files. The function checks for available translations based on the language code provided in the URL, and if the language is not available, it redirects to the file download route. It also ensures that users cannot access directories outside of the designated downloads folder by validating the requested path. The function generates a list of items (files and folders) to be displayed on the page, including their icons, names, links, sizes, and modification dates, and renders an HTML template with this information.

    Args:
        language_code (str): The language code extracted from the URL, used to determine the translation to be applied to the interface.

    Returns:
        Response: A Flask response object containing the rendered HTML page with the list of files and folders, or a redirect to the file download route if the language is not available.
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
        return abort(404)
    if not current_directory.is_dir():
        return abort(404)
    translator = get_translator(language_code)
    items: list[dict[str, Any]] = []
    if current_directory != root_directory:
        parent_directory: Path = current_directory.parent
        link: str = (
            f"/{language_code}"
            if parent_directory == root_directory
            else f"/{language_code}?dir={quote(str(parent_directory.relative_to(root_directory)))}"
        )
        items.append(
            {
                "icon": "fas fa-level-up-alt",
                "name": translator.gettext("Previous Folder"),
                "link": link,
            }
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
            mime_main_type: str = mime_type.split("/")[0] if mime_type else ""
            icon: str = MIME_ICON_MAP.get(
                mime_type or "", MIME_ICON_MAP.get(mime_main_type, "fas fa-file")
            )

            file_size_bytes: int = file_stat.st_size
            size_index: int = min(4, max(0, (file_size_bytes.bit_length() - 1) // 10))
            file_size: float = file_size_bytes / (1024**size_index)
            items.append(
                {
                    "icon": icon,
                    "name": entry_path.name,
                    "link": f"/{quote(str(entry_path.relative_to(root_directory)))}",
                    "size": f"{file_size:.2f}{SIZE_UNITS[size_index]}",
                    "date": datetime.datetime.fromtimestamp(
                        file_stat.st_mtime, UTC
                    ).isoformat(timespec="seconds"),
                }
            )
        else:
            items.append(
                {
                    "icon": "fas fa-folder-open",
                    "name": entry_path.name,
                    "link": f"/{language_code}?dir={quote(str(entry_path.relative_to(root_directory)))}",
                }
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
    """
    Serve the LICENSE file as plain text when the /LICENSE route is accessed. This allows users to view the license information directly in their browser without needing to download the file.

    Returns:
        Response: A Flask response object containing the contents of the LICENSE file with a MIME type of "text/plain".
    """
    return send_file("LICENSE", mimetype="text/plain")


@app.get("/<path:requested_filename>")
def download_file(requested_filename: str) -> Response:
    """
    Serve a file for download when a specific filename is requested. The function checks if the requested file exists within the designated downloads directory and ensures that the path is valid to prevent unauthorized access to files outside of this directory. If the file exists and is valid, it is sent to the user as an attachment for download. If the file does not exist or the path is invalid, appropriate HTTP error responses are returned.

    Args:
        requested_filename (str): The filename extracted from the URL, representing the file that the user wants to download.

    Returns:
        Response: A Flask response object that either contains the requested file for download or an error message if the file does not exist or the path is invalid.
    """
    root_directory: Path = (Path(__file__).parent / "downloads").resolve()
    entry_path: Path = (root_directory / requested_filename).resolve()
    try:
        entry_path.relative_to(root_directory)
    except ValueError:
        abort(403)
    if not entry_path.is_file():
        return abort(404)
    return send_file(str(entry_path), as_attachment=True, conditional=True)


@app.errorhandler(HTTPException)
def handle_error(exception: HTTPException) -> Response:
    """
    Handle HTTP exceptions by rendering a custom error page based on the status code of the exception. The function checks the status code of the exception and selects an appropriate HTML template to display a user-friendly error message. If the status code is not one of the predefined ones (400, 401, 403, 404, 500, 503), it defaults to using the template for a 500 Internal Server Error.

    Args:
        exception (HTTPException): The HTTP exception that was raised during the request handling process.

    Returns:
        Response: A Flask response object containing the rendered error page with the appropriate status code and MIME type of "text/html".
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
    """
    Minify HTML responses to reduce the size of the content sent to the client. This function checks if the response's MIME type is "text/html" and if it is not a direct passthrough response. If both conditions are met, it uses the minify_html library to minify the HTML content by removing unnecessary whitespace, comments, and optionally minifying embedded CSS and JavaScript. The minified HTML is then set as the new response data before being returned to the client.

    Args:
        response (Response): The Flask response object that is being processed after the request has been handled.

    Returns:
        Response: The modified Flask response object with minified HTML content if applicable, or the original response if the conditions for minification are not met.
    """
    if response.mimetype == "text/html" and not response.direct_passthrough:
        response.set_data(
            minify_html.minify(
                response.get_data(as_text=True),
                keep_comments=False,
                minify_css=True,
                minify_js=True,
            )
        )
    return response


if __name__ == "__main__":
    app.run(debug=True)

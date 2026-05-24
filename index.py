import datetime
import mimetypes
import os
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
Compress(app)


@app.route("/", methods=["GET"])
async def redirect_to_default_lang() -> Response:
    """
    Redirect root URL to default language directory.

    Constructs the redirect URL by prepending "/en" to the original request path, preserving query parameters if present.

    Returns:
        Response: A Flask redirect response to the default language directory.
    """
    url = "/en" + (request.full_path[1:] if "?" in request.full_path else "")
    return redirect(url, code=302)


@app.route("/<lang_code>", methods=["GET"])
async def index(lang_code: str) -> Response:
    """
    Serve the index page for a given language code, displaying a list of files and directories.

    Args:
        lang_code (str): The language code for which to serve the index page.

    Returns:
        Response: A Flask response containing the rendered index page with the list of files and directories, or a redirect to the file download if the language code is not valid.
    """
    valid_languages = {
        d.name
        for d in Path("languages").iterdir()
        if d.is_dir() and (d / "LC_MESSAGES" / "messages.mo").exists()
    }
    if lang_code not in valid_languages:
        return await download_file(lang_code)
    safe_root = (Path(__file__).resolve().parent / "downloads").resolve()
    user_dir = request.args.get("dir", "")
    if Path(user_dir).is_absolute():
        return abort(404)
    directory = (safe_root / user_dir).resolve()
    if safe_root not in directory.parents and directory != safe_root:
        return abort(404)
    _ = get_translator(lang_code).gettext
    file_list = []
    if directory != safe_root:
        parent_dir = directory.parent
        link = (
            f"/{lang_code}"
            if parent_dir == safe_root
            else f"/{lang_code}?dir={parent_dir.relative_to(safe_root)}"
        )
        file_list.append(
            {
                "icon": "fas fa-level-up-alt",
                "name": _("Previous Folder"),
                "link": link,
            }
        )
    ignore_files = set(os.getenv("IGNORE_FILES", "").split(","))
    for file_path in directory.iterdir():
        name = file_path.name
        if name.startswith(".") or name in ignore_files:
            continue
        mime_type, _ = mimetypes.guess_type(str(file_path))
        main = mime_type.split("/")[0] if mime_type else ""
        if file_path.is_dir():
            icon = "folder-open"
        elif main in ("image", "video", "audio", "font"):
            icon = f"file-{main}"
        elif main == "text":
            icon = "file-alt"
        elif main == "application":
            icon = "file-code"
        else:
            icon = "file"
        if file_path.is_file():
            size_bytes = file_path.stat().st_size
            idx = min(4, max(0, (size_bytes.bit_length() - 1) // 10))
            size_units = ["B", "KB", "MB", "GB", "TB"]
            size = size_bytes / (1024**idx)
            file_list.append(
                {
                    "ext": icon,
                    "name": name,
                    "link": f"/{quote(str(file_path.relative_to(safe_root)))}",
                    "size": f"{size:.2f}{size_units[idx]}",
                    "date": datetime.datetime.fromtimestamp(
                        file_path.stat().st_mtime, datetime.timezone.utc
                    ).isoformat(timespec="seconds"),
                }
            )
        else:
            file_list.append(
                {
                    "ext": icon,
                    "name": name,
                    "link": f"/{lang_code}?dir={quote(str(file_path.relative_to(safe_root)))}",
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


@app.route("/LICENSE", methods=["GET"])
async def show_license() -> Response:
    """
    Serve the LICENSE file as plain text.

    Returns:
        Response: A Flask response containing the contents of the LICENSE file with MIME type "text/plain".
    """
    return send_file("LICENSE", mimetype="text/plain")


@app.route("/<path:filename>", methods=["GET"])
async def download_file(filename: str) -> Response:
    """
    Serve a file for download, ensuring the file is within the allowed directory and not in the ignore list.

    Args:
        filename (str): The path of the file to be downloaded, relative to the safe root directory.

    Returns:
        Response: A Flask response that initiates the file download if the file is valid, or an appropriate error response if the file is not found or access is forbidden.
    """
    safe_root = Path(__file__).parent / "downloads"
    file_path = (safe_root / filename).resolve()
    if not file_path.is_file():
        return abort(404)
    if safe_root not in file_path.parents:
        return abort(403)
    ignore_files = set(os.getenv("IGNORE_FILES", "").split(","))
    for part in Path(filename).parts:
        if part in ignore_files:
            return abort(403)
    return send_file(file_path, as_attachment=True)


@app.errorhandler(Exception)
async def handle_error(error: Exception) -> Response:
    """
    Handle exceptions by returning a custom error page based on the error code.

    Args:
        error (Exception): The exception that occurred.

    Returns:
        Response: A Flask response containing the rendered error page with the appropriate status code.
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

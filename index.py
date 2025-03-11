import datetime
import glob
import mimetypes
import os
import re

import aiohttp
import yaml
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template_string,
    request,
    send_file,
)

app = Flask(__name__, static_folder="")
__import__("flask_compress").Compress(app)
load_dotenv(dotenv_path=".env")


def load_translation(language):
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")
    file_path = os.path.normpath(
        os.path.join(
            base_path,
            f"{language}.yaml",
        )
    )
    if not file_path.startswith(base_path):
        raise Exception("Invalid translation file path")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise FileNotFoundError(f"Translation file not found: translations/{language}.yaml")


@app.route("/", methods=["GET"])
def redirect_to_default_lang():
    query_string = request.query_string.decode("utf-8")
    new_url = "/en"
    if query_string:
        new_url += f"?{query_string}"
    return redirect(new_url, code=302)


@app.route("/<lang>", methods=["GET"])
def index(lang):
    valid_languages = {
        filename[:-5]
        for filename in os.listdir("translations")
        if re.compile(r"^[a-z]{2}\.yaml$", re.IGNORECASE).match(filename)
    }
    if lang not in valid_languages:
        return download_file(lang)
    translations = load_translation(lang)
    font_family = os.getenv("font_family")
    favicon = os.getenv("favicon")
    theme_color = os.getenv("theme_color")
    safe_root = os.path.dirname(__file__)
    directory = request.args.get("dir") or safe_root
    directory = os.path.normpath(os.path.join(safe_root, directory))
    if not directory.startswith(safe_root) or not os.path.isdir(directory):
        return abort(404)
    file_list = (
        [
            {
                "icon": "fas fa-level-up-alt",
                "name": translations["Parent_Directory"],
                "link": (
                    f"/{lang}?dir={os.path.dirname(directory)}"
                    if os.path.dirname(directory)
                    else f"/{lang}"
                ),
            }
        ]
        if directory != os.path.dirname(__file__)
        else []
    )
    for file in sorted(
        {file for file in os.listdir(directory) if not file.startswith(".")}
    ):
        if file in os.getenv("ignore_files", "").split(","):
            continue
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            icon_class = "fas fa-file"
            if mime_type:
                if mime_type.startswith("video"):
                    icon_class = "fas fa-video"
                elif mime_type.startswith("image"):
                    icon_class = "fas fa-image"
                elif mime_type.startswith("audio"):
                    icon_class = "fas fa-music"
                elif mime_type.endswith("python"):
                    icon_class = "fab fa-python"
                elif mime_type == "application/pdf":
                    icon_class = "fas fa-file-pdf"
                elif mime_type.startswith("application/msword"):
                    icon_class = "fas fa-file-word"
                elif mime_type.startswith("application/vnd.ms-excel"):
                    icon_class = "fas fa-file-excel"
                elif mime_type.startswith("application/vnd.ms-powerpoint"):
                    icon_class = "fas fa-file-powerpoint"
                elif mime_type.startswith("application/zip") or mime_type.startswith(
                    "application/x-rar-compressed"
                ):
                    icon_class = "fas fa-file-archive"
                elif mime_type == "text/html":
                    icon_class = "fab fa-html5"
                elif mime_type == "text/css":
                    icon_class = "fab fa-css3"
                elif mime_type == "application/json":
                    icon_class = "fas fa-file-code"
                elif mime_type == "application/javascript":
                    icon_class = "fab fa-js"
                elif mime_type.startswith("text/plain"):
                    icon_class = "fas fa-file-alt"
            file_list.append(
                {
                    "icon": icon_class,
                    "name": file,
                    "link": f"/{os.path.relpath(file_path, os.path.dirname(__file__))}",
                    "size": f'{os.path.getsize(file_path) / (1024 ** (index := max(0, min(4, (os.path.getsize(file_path).bit_length() - 1) // 10)))):.2f}{"B KB MB GB TB".split()[index]}',
                    "date": datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        else:
            file_list.append(
                {
                    "icon": "fas fa-folder-open",
                    "name": file,
                    "link": f"/{lang}?dir={os.path.relpath(file_path, os.path.dirname(__file__))}",
                }
            )
    return render_template_string(
        """
<!doctype html>
<html dir="{{ translations['head']['dir'] }}" lang="{{ lang }}">

<head>
    <meta charset="UTF-8">
    <title>{{ translations['directory_listing'] }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="{{ theme_color }}">
    <meta name="title" content="{{ translations['head']['title'] }} - {{ ' '.join(request.host.split(':')[0].split('.')[:-1]) }}">
    <meta name="description" content="{{ translations['head']['description'] }}">
    <meta property="og:title" content="{{ translations['head']['title'] }} - {{ ' '.join(request.host.split(':')[0].split('.')[:-1]) }}">
    <meta property="og:description" content="{{ translations['head']['description'] }}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{{ request.url_root }}">
    <meta property="og:image" content="{{ favicon }}">
    <meta property="og:site_name" content="{{ ' '.join(request.host.split(':')[0].split('.')[:-1]) }}">
    <meta property="og:locale" content="{{ lang }}">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
        font-family: {{ font_family }};
        margin: 20px;
        background-color: #f9f9f9;
        color: #333;
        }
        h1 {
        text-align: center;
        color: #555;
        }
        .table-container {
        max-width: 100%;
        margin: 0 auto;
        overflow-x: auto;
        }
        table {
        border-collapse: collapse;
        width: 100%;
        background-color: #fff;
        box-shadow: 0 0 10px rgba(0, 0, 0, .1);
        margin-bottom: 20px;
        }
        td, th {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
        }
        th {
        background-color: #f2f2f2;
        cursor: pointer;
        }
        th.sortable:hover {
        background-color: #e0e0e0;
        }
        .icon {
        text-align: center;
        width: 30px;
        }
        a {
        text-decoration: none;
        color: #007bff;
        font-weight: 700;
        }
        a:hover {
        text-decoration: underline;
        }
        .search-bar {
        margin-bottom: 20px;
        text-align: center;
        }
        .search-bar input[type="text"] {
        width: 300px;
        max-width: 80%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        }
        .search-bar button {
        padding: 10px 20px;
        border: none;
        background-color: #007bff;
        color: #fff;
        border-radius: 4px;
        cursor: pointer;
        }
        .search-bar button:hover {
        background-color: #0056b3;
        }
        @media (max-width: 576px) {
        .search-bar input[type="text"] {
        width: 80%;
        }
        }
    </style>
</head>

<body>
    <h1>{{ translations['directory_listing'] }}</h1>
    <div class="search-bar"> <input oninput="filterTable(this.value)" placeholder="{{ translations['body']['search_placeholder'] }}"> </div>
    <div class="table-container">
        <table class="table table-hover table-striped">
            <thead>
                <tr>
                    <th class="icon">{{ translations['body']['file'] }}</th>
                    <th class="sortable" onclick="sortTable(1)">{{ translations['body']['name'] }}</th>
                    <th class="sortable" onclick="sortTable(2)">{{ translations['body']['size'] }}</th>
                    <th class="sortable" onclick="sortTable(3)">{{ translations['body']['last_modified'] }}</th>
                </tr>
            </thead>
            <tbody id="fileTableBody"> {% for file in file_list %} <tr>
                    <td class="icon"><i class="{{ file.icon }}"></i></td>
                    <td><a href="{{ file.link }}">{{ file.name }}</a></td>
                    <td>{{ file.size }}</td>
                    <td>{{ file.date }}</td>
                </tr> {% endfor %} </tbody>
        </table>
    </div>
    <script>
        function sortTable(e) {
        const tbody = document.querySelector("table tbody");
        const rows = Array.from(tbody.rows);
        const isSameColumn = e === window.lastSortedColumnIndex;
        const isAsc = isSameColumn && window.lastSortOrder === "asc";
        const sortedRows = rows.sort((a, b) => {
        let aText = a.cells[e].innerText.toLowerCase();
        let bText = b.cells[e].innerText.toLowerCase();
        if (e === 2) { // Size
        aText = parseFloat(aText);
        bText = parseFloat(bText);
        } else if (e === 3) { // Last modified
        aText = new Date(aText);
        bText = new Date(bText);
        }
        if (isAsc) {
        return aText > bText ? -1 : aText < bText ? 1 : 0;
        } else {
        return aText > bText ? 1 : aText < bText ? -1 : 0;
        }
        });
        while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
        }
        sortedRows.forEach(row => tbody.appendChild(row));
        window.lastSortedColumnIndex = e;
        window.lastSortOrder = isSameColumn && isAsc ? "desc" : "asc";
        const parentDirRow = sortedRows.find(row => row.cells[1].innerText === "Parent Directory");
        if (parentDirRow) {
        tbody.prepend(parentDirRow);
        }
        }

        function filterTable(filterText) {
        document.querySelectorAll("#fileTableBody tr").forEach(row => {
        row.cells[1].innerText.toLowerCase().includes(filterText.toLowerCase())
        ? row.style.display = ""
        : row.style.display = "none";
        });
        }
    </script>
</body>

</html>
""",
        file_list=file_list,
        lang=lang,
        translations=translations,
        font_family=font_family,
        favicon=favicon,
        theme_color=theme_color,
    )


@app.route("/<path:filename>", methods=["GET"])
def download_file(filename):
    file_path = os.path.normpath(os.path.join(os.path.dirname(__file__), filename))
    for part in filename.split("/"):
        if part in set(os.getenv("ignore_files", "").split(",")):
            return abort(403)
    if os.path.isfile(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.split("/")[0] in {
            "image",
            "audio",
            "video",
            "text",
            "application",
        }:
            return send_file(file_path, mimetype=mime_type)
        return send_file(file_path, as_attachment=True)
    return abort(404)


@app.route("/favicon.ico", methods=["GET"])
async def favicon():
    async with aiohttp.ClientSession() as session:
        async with session.get(os.getenv("favicon")) as response:
            return Response(await response.read(), mimetype="image/x-icon")


@app.errorhandler(Exception)
def handle_error(error):
    error_pages = {
        400: "400",
        401: "401",
        403: "403",
        404: "404",
        500: "500",
        503: "503",
    }
    return redirect(
        f"https://error.robonamari.com/{error_pages.get(getattr(error, 'code', 500), '500')}",
        code=302,
    )


if __name__ == "__main__":
    app.run(
        host=os.getenv("host"),
        port=os.getenv("port"),
        use_reloader=os.getenv("use_reloader"),
        debug=os.getenv("debug"),
        extra_files=glob.glob(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "*")
        ),
    )

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
<html dir="{{translations['head']['dir']}}" lang="{{lang}}">

<head>
  <meta charset="UTF-8">
  <title>{{translations['directory_listing']}}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="title" content="{{directory_listing}} - {{' '.join(request.host.split(':')[0].split('.')[:-1])}}">
  <meta name="description" content="{{translations['head']['description']}}">
  <meta name="theme-color" content="{{theme_color}}">
  <meta property="og:title" content="{{directory_listing}} - {{' '.join(request.host.split(':')[0].split('.')[:-1])}}">
  <meta property="og:description" content="{{translations['head']['description']}}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{{request.url_root}}">
  <meta property="og:image" content="{{favicon}}">
  <meta property="og:site_name" content="{{' '.join(request.host.split(':')[0].split('.')[:-1])}}">
  <meta property="og:locale" content="{{lang}}">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
  <style>
    *,::after,::before{box-sizing:border-box}html{line-height:1.15;-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent}body{margin:0;font-size:1rem;font-weight:400;line-height:1.5;color:#212529;text-align:left;background-color:#fff}h1{margin-top:0;margin-bottom:.5rem}a{color:#007bff;text-decoration:none;background-color:transparent}a:hover{color:#0056b3;text-decoration:underline}table{border-collapse:collapse}th{text-align:inherit}input{margin:0;font-size:inherit;line-height:inherit}input{overflow:visible}h1{margin-bottom:.5rem;font-weight:500;line-height:1.2}h1{font-size:2.5rem}.table{width:100%;margin-bottom:1rem;color:#212529}.table td,.table th{padding:.75rem;vertical-align:top;border-top:1px solid #dee2e6}.table thead th{vertical-align:bottom;border-bottom:2px solid #dee2e6}.table-striped tbody tr:nth-of-type(odd){background-color:rgba(0,0,0,.05)}.table-hover tbody tr:hover{color:#212529;background-color:rgba(0,0,0,.075)}.custom-control-input.is-valid:focus:not(:checked)~.custom-control-label::before,.was-validated .custom-control-input:valid:focus:not(:checked)~.custom-control-label::before{border-color:#28a745}.custom-control-input.is-invalid:focus:not(:checked)~.custom-control-label::before,.was-validated .custom-control-input:invalid:focus:not(:checked)~.custom-control-label::before{border-color:#dc3545}.btn:not(:disabled):not(.disabled){cursor:pointer}.btn-primary:not(:disabled):not(.disabled).active,.btn-primary:not(:disabled):not(.disabled):active{color:#fff;background-color:#0062cc;border-color:#005cbf}.btn-primary:not(:disabled):not(.disabled).active:focus,.btn-primary:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(38,143,255,.5)}.btn-secondary:not(:disabled):not(.disabled).active,.btn-secondary:not(:disabled):not(.disabled):active{color:#fff;background-color:#545b62;border-color:#4e555b}.btn-secondary:not(:disabled):not(.disabled).active:focus,.btn-secondary:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(130,138,145,.5)}.btn-success:not(:disabled):not(.disabled).active,.btn-success:not(:disabled):not(.disabled):active{color:#fff;background-color:#1e7e34;border-color:#1c7430}.btn-success:not(:disabled):not(.disabled).active:focus,.btn-success:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(72,180,97,.5)}.btn-info:not(:disabled):not(.disabled).active,.btn-info:not(:disabled):not(.disabled):active{color:#fff;background-color:#117a8b;border-color:#10707f}.btn-info:not(:disabled):not(.disabled).active:focus,.btn-info:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(58,176,195,.5)}.btn-warning:not(:disabled):not(.disabled).active,.btn-warning:not(:disabled):not(.disabled):active{color:#212529;background-color:#d39e00;border-color:#c69500}.btn-warning:not(:disabled):not(.disabled).active:focus,.btn-warning:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(222,170,12,.5)}.btn-danger:not(:disabled):not(.disabled).active,.btn-danger:not(:disabled):not(.disabled):active{color:#fff;background-color:#bd2130;border-color:#b21f2d}.btn-danger:not(:disabled):not(.disabled).active:focus,.btn-danger:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(225,83,97,.5)}.btn-light:not(:disabled):not(.disabled).active,.btn-light:not(:disabled):not(.disabled):active{color:#212529;background-color:#dae0e5;border-color:#d3d9df}.btn-light:not(:disabled):not(.disabled).active:focus,.btn-light:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(216,217,219,.5)}.btn-dark:not(:disabled):not(.disabled).active,.btn-dark:not(:disabled):not(.disabled):active{color:#fff;background-color:#1d2124;border-color:#171a1d}.btn-dark:not(:disabled):not(.disabled).active:focus,.btn-dark:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(82,88,93,.5)}.btn-outline-primary:not(:disabled):not(.disabled).active,.btn-outline-primary:not(:disabled):not(.disabled):active{color:#fff;background-color:#007bff;border-color:#007bff}.btn-outline-primary:not(:disabled):not(.disabled).active:focus,.btn-outline-primary:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(0,123,255,.5)}.btn-outline-secondary:not(:disabled):not(.disabled).active,.btn-outline-secondary:not(:disabled):not(.disabled):active{color:#fff;background-color:#6c757d;border-color:#6c757d}.btn-outline-secondary:not(:disabled):not(.disabled).active:focus,.btn-outline-secondary:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(108,117,125,.5)}.btn-outline-success:not(:disabled):not(.disabled).active,.btn-outline-success:not(:disabled):not(.disabled):active{color:#fff;background-color:#28a745;border-color:#28a745}.btn-outline-success:not(:disabled):not(.disabled).active:focus,.btn-outline-success:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(40,167,69,.5)}.btn-outline-info:not(:disabled):not(.disabled).active,.btn-outline-info:not(:disabled):not(.disabled):active{color:#fff;background-color:#17a2b8;border-color:#17a2b8}.btn-outline-info:not(:disabled):not(.disabled).active:focus,.btn-outline-info:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(23,162,184,.5)}.btn-outline-warning:not(:disabled):not(.disabled).active,.btn-outline-warning:not(:disabled):not(.disabled):active{color:#212529;background-color:#ffc107;border-color:#ffc107}.btn-outline-warning:not(:disabled):not(.disabled).active:focus,.btn-outline-warning:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(255,193,7,.5)}.btn-outline-danger:not(:disabled):not(.disabled).active,.btn-outline-danger:not(:disabled):not(.disabled):active{color:#fff;background-color:#dc3545;border-color:#dc3545}.btn-outline-danger:not(:disabled):not(.disabled).active:focus,.btn-outline-danger:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(220,53,69,.5)}.btn-outline-light:not(:disabled):not(.disabled).active,.btn-outline-light:not(:disabled):not(.disabled):active{color:#212529;background-color:#f8f9fa;border-color:#f8f9fa}.btn-outline-light:not(:disabled):not(.disabled).active:focus,.btn-outline-light:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(248,249,250,.5)}.btn-outline-dark:not(:disabled):not(.disabled).active,.btn-outline-dark:not(:disabled):not(.disabled):active{color:#fff;background-color:#343a40;border-color:#343a40}.btn-outline-dark:not(:disabled):not(.disabled).active:focus,.btn-outline-dark:not(:disabled):not(.disabled):active:focus{box-shadow:0 0 0 .2rem rgba(52,58,64,.5)}.custom-control-input:focus:not(:checked)~.custom-control-label::before{border-color:#80bdff}.custom-control-input:not(:disabled):active~.custom-control-label::before{color:#fff;background-color:#b3d7ff;border-color:#b3d7ff}.close:not(:disabled):not(.disabled):focus,.close:not(:disabled):not(.disabled):hover{opacity:.75}@supports((position:-webkit-sticky)or(position:sticky)){}@media print{*,::after,::before{text-shadow:none!important;box-shadow:none!important}a:not(.btn){text-decoration:underline}thead{display:table-header-group}tr{page-break-inside:avoid}@page{size:a3}body{min-width:992px!important}.table{border-collapse:collapse!important}.table td,.table th{background-color:#fff!important}}body{font-family:{{font_family}};margin:20px;background-color:#f9f9f9;color:#333}h1{text-align:center;color:#555}.table-container{max-width:100%;margin:0 auto;overflow-x:auto}table{border-collapse:collapse;width:100%;background-color:#fff;box-shadow:0 0 10px rgba(0,0,0,.1);margin-bottom:20px}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd}th{background-color:#f2f2f2;cursor:pointer}th.sortable:hover{background-color:#e0e0e0}.icon{text-align:center;width:30px}a{text-decoration:none;color:#007bff;font-weight:700}a:hover{text-decoration:underline}.search-bar{margin-bottom:20px;text-align:center}.search-bar input[type="text"]{width:300px;max-width:80%;padding:10px;border:1px solid #ddd;border-radius:4px}@media(max-width:576px){.search-bar input[type="text"]{width:80%}}
  </style>
</head>

<body>
  <h1>{{ translations['directory_listing'] }}</h1>
  <div class="search-bar"> <input oninput="filterTable(this.value)" placeholder="{{translations['body']['search_placeholder']}}"> </div>
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
          <td class="icon"><i class="{{file.icon}}"></i></td>
          <td><a href="{{file.link}}">{{file.name}}</a></td>
          <td>{{file.size}}</td>
          <td>{{file.date}}</td>
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
    safe_root = os.path.dirname(__file__)
    file_path = os.path.normpath(os.path.join(safe_root, filename))
    if not file_path.startswith(safe_root):
        return abort(403)
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

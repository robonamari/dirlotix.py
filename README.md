<div align="center">

[**🇮🇷 فارسی**](.github/README/fa.md)
</div>

<p align="center">
    <img src="https://img.shields.io/github/languages/code-size/robonamari/Dirlotix-py?style=flat" alt="Code Size">
    <img src="https://tokei.rs/b1/github/robonamari/Dirlotix-py?style=flat" alt="Total lines">
    <img src="https://img.shields.io/badge/python-%5E3.9-blue" alt="Python Versions">
    <img src="https://img.shields.io/github/license/robonamari/Dirlotix-py" alt="GitHub license">
</p>

---

This project is a file manager web application built with Python and Flask. It allows users to browse and download files on a server, view directory listings, and interact with different file types. The application also supports multi-language functionality and allows configuration of various settings like theme colors, fonts, and favicon.

## Features
- Browse and view files and directories.
- Support for various file types (images, videos, audio, text, PDFs, and more).
- Search and sort files by name, size, or last modified date.
- Support for all living languages with dynamic loading via YAML files (based on the [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) standard, covering approximately 176 languages).
- Configurable theme colors, fonts, and favicon.
- Error handling and redirection for various HTTP errors.
## Self-host Configuration
<details>
<summary>4 Steps to Host Your Own Dirlotix-py</summary>

### 1. Clone the Repository
```bash
git clone https://github.com/robonamari/Dirlotix-py
```

### 2. Install Python and Dependencies
Install Python, then install the required Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure the Script
1. Rename **.env.example** to **.env**.
2. The full descriptions of the environment variables are written inside the `.env` file, and you need to fill them out accordingly.

### 4. Run the Script
```bash
python index.py
```

### Done!
Your script should be fully configured and ready to run!

</details>

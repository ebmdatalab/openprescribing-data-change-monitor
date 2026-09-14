import os
import shutil

from jinja2 import Environment, FileSystemLoader


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
SITE_DIR = os.path.join(ROOT_DIR, "site")

template_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR)
)

RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/"
    "ebmdatalab/openprescribing-epd-new/main/assets/"
)


def copy_directory_contents(source_dir, destination_dir):
    """Copy all files and subdirectories from source to destination."""
    os.makedirs(destination_dir, exist_ok=True)

    for item in os.listdir(source_dir):
        source = os.path.join(source_dir, item)
        destination = os.path.join(destination_dir, item)

        if os.path.isdir(source):
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True,
            )
        else:
            shutil.copy2(source, destination)


def copy_html_file(source_path, destination_path):
    """
    Copy an HTML file while replacing the temporary raw GitHub
    asset URLs with paths to the local site/assets directory.
    """
    with open(source_path, "r", encoding="utf-8") as file:
        html = file.read()

    destination_dir = os.path.dirname(destination_path)

    relative_assets = os.path.relpath(
        os.path.join(SITE_DIR, "assets"),
        destination_dir,
    ).replace(os.sep, "/")

    asset_prefix = f"{relative_assets}/"

    html = html.replace(
        f"{RAW_GITHUB_BASE}report.css",
        f"{asset_prefix}report.css",
    )

    html = html.replace(
        f"{RAW_GITHUB_BASE}op_logo.png",
        f"{asset_prefix}op_logo.png",
    )

    html = html.replace(
        f"{RAW_GITHUB_BASE}oph_logo.png",
        f"{asset_prefix}oph_logo.png",
    )

    os.makedirs(destination_dir, exist_ok=True)

    with open(destination_path, "w", encoding="utf-8") as file:
        file.write(html)


def copy_reports():
    """Copy the reports directory into site/, rewriting HTML asset paths."""
    for root, dirs, files in os.walk(REPORTS_DIR):
        relative_root = os.path.relpath(root, REPORTS_DIR)

        if relative_root == ".":
            destination_root = SITE_DIR
        else:
            destination_root = os.path.join(
                SITE_DIR,
                relative_root,
            )

        os.makedirs(destination_root, exist_ok=True)

        for filename in files:
            source_path = os.path.join(root, filename)
            destination_path = os.path.join(
                destination_root,
                filename,
            )

            if filename.endswith(".html"):
                copy_html_file(
                    source_path,
                    destination_path,
                )
            else:
                shutil.copy2(
                    source_path,
                    destination_path,
                )


def build_index_page():
    """Generate the top-level site index page."""
    template = template_env.get_template("index.html")

    html = template.render(
        stylesheet_url="assets/report.css",
        logo_url="assets/op_logo.png",
    )

    output_path = os.path.join(
        SITE_DIR,
        "index.html",
    )

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)


def build_site():
    """Build the complete static website."""
    # Remove the existing site.
    if os.path.exists(SITE_DIR):
        shutil.rmtree(SITE_DIR)

    os.makedirs(SITE_DIR)

    # Copy assets.
    copy_directory_contents(
        ASSETS_DIR,
        os.path.join(SITE_DIR, "assets"),
    )

    # Copy reports and rewrite their asset URLs.
    copy_reports()

    # Generate the homepage.
    build_index_page()

    print(f"Site built in {SITE_DIR}")


if __name__ == "__main__":
    build_site()
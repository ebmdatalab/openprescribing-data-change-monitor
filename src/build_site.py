import os
import shutil

import pandas as pd
from jinja2 import Environment, FileSystemLoader


ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
SITE_DIR = os.path.join(ROOT_DIR, "site")

template_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR)
)

RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/"
    "ebmdatalab/openprescribing-data-change-monitor/main/assets/"
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
    Copy an HTML file while replacing temporary external URLs
    with paths appropriate for the static site.
    """
    with open(source_path, "r", encoding="utf-8") as file:
        html = file.read()

    destination_dir = os.path.dirname(destination_path)

    # Work out the relative path from this HTML file to site/assets/
    relative_assets = os.path.relpath(
        os.path.join(SITE_DIR, "assets"),
        destination_dir,
    ).replace(os.sep, "/")

    asset_prefix = f"{relative_assets}/"

    # CSS
    html = html.replace(
        f"{RAW_GITHUB_BASE}report.css",
        f"{asset_prefix}report.css",
    )

    # Logos
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
    """Copy reports into site/, rewriting HTML asset and navigation URLs."""
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
    """Generate the top-level website index page."""
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


def build_report_list_page(
    source_directory,
    output_path,
    title,
    logo_filename,
    logo_alt,
):
    """Generate a report index page from reports in a directory."""

    html_files = [
        filename
        for filename in os.listdir(source_directory)
        if (
            filename.endswith(".html")
            and not filename.startswith("list_")
            and filename != "index.html"
        )
    ]

    def extract_date(filename):
        return filename.split("_")[-1].replace(".html", "")

    # Newest report first.
    html_files = sorted(
        html_files,
        key=extract_date,
        reverse=True,
    )

    reports = []

    for filename in html_files:
        date_part = extract_date(filename)

        try:
            report_title = pd.to_datetime(
                date_part
            ).strftime("%B %Y")
        except (ValueError, TypeError):
            report_title = date_part

        reports.append({
            "title": report_title,
            "url": filename,
        })

    template = template_env.get_template("report_list.html")

    output_directory = os.path.dirname(output_path)

    # Calculate relative path from the list page to site/assets/.
    relative_assets = os.path.relpath(
        os.path.join(SITE_DIR, "assets"),
        output_directory,
    ).replace(os.sep, "/")

    asset_prefix = f"{relative_assets}/"

    html = template.render(
        title=title,
        logo_url=f"{asset_prefix}{logo_filename}",
        logo_alt=logo_alt,
        stylesheet_url=f"{asset_prefix}report.css",
        reports=reports,
    )

    os.makedirs(output_directory, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)


def build_report_list_pages():
    """Generate EPD, EPD test and SCMD report index pages."""

    # EPD change reports
    build_report_list_page(
        source_directory=os.path.join(
            SITE_DIR,
            "epd",
            "changes",
        ),
        output_path=os.path.join(
            SITE_DIR,
            "epd",
            "changes",
            "index.html",
        ),
        title="English Prescribing Data - Monthly New Items Reports",
        logo_filename="op_logo.png",
        logo_alt="OpenPrescribing logo",
    )

    # EPD test reports
    build_report_list_page(
        source_directory=os.path.join(
            SITE_DIR,
            "epd",
            "tests",
        ),
        output_path=os.path.join(
            SITE_DIR,
            "epd",
            "tests",
            "index.html",
        ),
        title="English Prescribing Data - Monthly Test Reports",
        logo_filename="op_logo.png",
        logo_alt="OpenPrescribing logo",
    )

    # SCMD change reports
    build_report_list_page(
        source_directory=os.path.join(
            SITE_DIR,
            "scmd",
            "changes",
        ),
        output_path=os.path.join(
            SITE_DIR,
            "scmd",
            "changes",
            "index.html",
        ),
        title="Secondary Care Medicines Data - Monthly New Items Reports",
        logo_filename="oph_logo.png",
        logo_alt="OpenPrescribing Hospitals logo",
    )


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

    # Copy reports and rewrite their asset/navigation URLs.
    copy_reports()

    # Generate website pages.
    build_index_page()
    build_report_list_pages()

    print(f"Site built in {SITE_DIR}")


if __name__ == "__main__":
    build_site()
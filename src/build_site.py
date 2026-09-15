import os
import shutil

import pandas as pd
from jinja2 import Environment, FileSystemLoader


ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(ROOT_DIR, "data")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
SITE_DIR = os.path.join(ROOT_DIR, "site")

template_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR)
)


def copy_directory_contents(source_dir, destination_dir):
    """Copy all files and subdirectories from source to destination."""
    if not os.path.isdir(source_dir):
        return

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


def read_csv_html(path):
    """Read a CSV file and return its HTML table."""
    dataframe = pd.read_csv(path)

    return dataframe.to_html(
        index=False,
        classes="table",
    )


def get_january_alert(date):
    """Return the appropriate January BNF change warning."""
    if date[-2:] != "01":
        return ""

    year = int(date[:4])

    bnf_change_styles = {
        2024: {
            "url": "https://www.nhsbsa.nhs.uk/bnf-code-changes-january-{year}",
            "description": "BNF code changes",
        },
        2025: {
            "url": "https://www.nhsbsa.nhs.uk/bnf-version-changes-january-{year}",
            "description": "BNF version changes",
        },
    }

    # Find the most recent rule that applies to this year.
    applicable_years = [
        rule_year
        for rule_year in bnf_change_styles
        if rule_year <= year
    ]

    if not applicable_years:
        return ""

    rule_year = max(applicable_years)
    rule = bnf_change_styles[rule_year]

    changes_url = rule["url"].format(year=year)
    changes_description = rule["description"]

    return (
        "<p><b>Please note:</b> January data often includes a larger number "
        'of "changes" due to annual BNF changes. '
        f'<a href="{changes_url}">'
        f"More information about {changes_description} for January {year}"
        "</a>.</p>"
    )


def render_epd_report(date):
    """Render one EPD change report from stored CSV data."""
    data_dir = os.path.join(
        DATA_DIR,
        "epd",
        "changes",
        date,
    )

    required_files = {
        "chemical_substances": os.path.join(
            data_dir,
            "chemical_substances.csv",
        ),
        "bnf_codes": os.path.join(
            data_dir,
            "bnf_codes.csv",
        ),
        "bnf_descriptions": os.path.join(
            data_dir,
            "bnf_descriptions.csv",
        ),
    }

    missing_files = [
        path
        for path in required_files.values()
        if not os.path.isfile(path)
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Missing EPD data files for {date}: "
            f"{missing_files}"
        )

    template = template_env.get_template(
        "monthly_report_epd.html"
    )

    return template.render(
        date=date,
        logo_url="../../assets/op_logo.png",
        stylesheet_url="../../assets/report.css",
        reports_index_url="index.html",
        january_alert=get_january_alert(date),
        chemical_substances=read_csv_html(
            required_files["chemical_substances"]
        ),
        bnf_codes=read_csv_html(
            required_files["bnf_codes"]
        ),
        bnf_descriptions=read_csv_html(
            required_files["bnf_descriptions"]
        ),
    )


def render_scmd_report(date):
    """Render one SCMD change report from stored CSV data."""
    data_dir = os.path.join(
        DATA_DIR,
        "scmd",
        "changes",
        date,
    )

    required_files = {
        "vtms": os.path.join(
            data_dir,
            "vtms.csv",
        ),
        "vmps": os.path.join(
            data_dir,
            "vmps.csv",
        ),
    }

    missing_files = [
        path
        for path in required_files.values()
        if not os.path.isfile(path)
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Missing SCMD data files for {date}: "
            f"{missing_files}"
        )

    template = template_env.get_template(
        "monthly_report_scmd.html"
    )

    return template.render(
        date=date,
        logo_url="../../assets/oph_logo.png",
        stylesheet_url="../../assets/report.css",
        reports_index_url="index.html",
        vtms=read_csv_html(
            required_files["vtms"]
        ),
        vmps=read_csv_html(
            required_files["vmps"]
        ),
    )


def get_data_dates(dataset, report_type):
    """Return available YYYY-MM report dates."""
    directory = os.path.join(
        DATA_DIR,
        dataset,
        report_type,
    )

    if not os.path.isdir(directory):
        return []

    dates = [
        name
        for name in os.listdir(directory)
        if (
            os.path.isdir(
                os.path.join(directory, name)
            )
            and len(name) == 7
            and name[4] == "-"
            and name[:4].isdigit()
            and name[5:].isdigit()
        )
    ]

    return sorted(
        dates,
        reverse=True,
    )


def build_epd_reports():
    """Build all EPD change reports from stored CSV data."""
    dates = get_data_dates(
        "epd",
        "changes",
    )

    output_dir = os.path.join(
        SITE_DIR,
        "epd",
        "changes",
    )

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    for date in dates:
        output_path = os.path.join(
            output_dir,
            f"monthly_report_{date}.html",
        )

        html = render_epd_report(date)

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(html)

        print(
            f"Built EPD report: monthly_report_{date}.html"
        )


def build_scmd_reports():
    """Build all SCMD change reports from stored CSV data."""
    dates = get_data_dates(
        "scmd",
        "changes",
    )

    output_dir = os.path.join(
        SITE_DIR,
        "scmd",
        "changes",
    )

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    for date in dates:
        output_path = os.path.join(
            output_dir,
            f"monthly_report_scmd_{date}.html",
        )

        html = render_scmd_report(date)

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(html)

        print(
            f"Built SCMD report: monthly_report_scmd_{date}.html"
        )


def build_index_page():
    """Generate the top-level website index page."""
    template = template_env.get_template(
        "index.html"
    )

    html = template.render(
        stylesheet_url="assets/report.css",
        logo_url="assets/op_logo.png",
    )

    output_path = os.path.join(
        SITE_DIR,
        "index.html",
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(html)


def build_report_list_page(
    source_directory,
    output_path,
    title,
    logo_filename,
    logo_alt,
):
    """Generate a report index page."""
    if not os.path.isdir(source_directory):
        os.makedirs(
            source_directory,
            exist_ok=True,
        )

    html_files = [
        filename
        for filename in os.listdir(
            source_directory
        )
        if (
            filename.endswith(".html")
            and not filename.startswith("list_")
            and filename not in {
                "index.html",
                "latest.html",
            }
        )
    ]

    def extract_date(filename):
        return filename.rsplit(
            "_",
            1,
        )[-1].replace(
            ".html",
            "",
        )

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

    template = template_env.get_template(
        "report_list.html"
    )

    output_directory = os.path.dirname(
        output_path
    )

    relative_assets = os.path.relpath(
        os.path.join(
            SITE_DIR,
            "assets",
        ),
        output_directory,
    ).replace(
        os.sep,
        "/",
    )

    asset_prefix = f"{relative_assets}/"

    html = template.render(
        title=title,
        logo_url=(
            f"{asset_prefix}{logo_filename}"
        ),
        logo_alt=logo_alt,
        stylesheet_url=(
            f"{asset_prefix}report.css"
        ),
        reports=reports,
    )

    os.makedirs(
        output_directory,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(html)


def build_report_list_pages():
    """Generate EPD, EPD test and SCMD report index pages."""

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
        title=(
            "English Prescribing Data - "
            "Monthly New Items Reports"
        ),
        logo_filename="op_logo.png",
        logo_alt="OpenPrescribing logo",
    )

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
        title=(
            "OpenPrescribing - "
            "Monthly Testing Review Reports"
        ),
        logo_filename="op_logo.png",
        logo_alt=(
            "OpenPrescribing development testing"
        ),
    )

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
        title=(
            "Secondary Care Medicines Data - "
            "Monthly New Items Reports"
        ),
        logo_filename="oph_logo.png",
        logo_alt=(
            "OpenPrescribing Hospitals logo"
        ),
    )


def copy_testing_reports():
    """
    Copy the existing testing HTML reports unchanged.

    Testing is intentionally still based on the existing HTML
    reports rather than the new data archive.
    """
    source_dir = os.path.join(
        REPORTS_DIR,
        "epd",
        "tests",
    )

    destination_dir = os.path.join(
        SITE_DIR,
        "epd",
        "tests",
    )

    if not os.path.isdir(source_dir):
        return

    os.makedirs(
        destination_dir,
        exist_ok=True,
    )

    for filename in os.listdir(source_dir):
        if (
            filename.endswith(".html")
            and filename != "index.html"
            and filename != "latest.html"
            and not filename.startswith("list_")
        ):
            source_path = os.path.join(
                source_dir,
                filename,
            )

            destination_path = os.path.join(
                destination_dir,
                filename,
            )

            shutil.copy2(
                source_path,
                destination_path,
            )

    print(
        "Copied existing testing reports."
    )


def build_latest_report(
    report_directory,
    filename_prefix,
):
    """
    Create latest.html as a copy of the newest dated report.
    """
    if not os.path.isdir(report_directory):
        return

    report_files = [
        filename
        for filename in os.listdir(
            report_directory
        )
        if (
            filename.startswith(
                filename_prefix
            )
            and filename.endswith(".html")
            and filename != "latest.html"
        )
    ]

    if not report_files:
        return

    def extract_date(filename):
        return filename.rsplit(
            "_",
            1,
        )[-1].replace(
            ".html",
            "",
        )

    latest_report = max(
        report_files,
        key=extract_date,
    )

    source_path = os.path.join(
        report_directory,
        latest_report,
    )

    destination_path = os.path.join(
        report_directory,
        "latest.html",
    )

    shutil.copy2(
        source_path,
        destination_path,
    )

    print(
        f"Latest report: "
        f"{latest_report} -> latest.html"
    )


def build_latest_reports():
    """Create latest.html permalinks."""

    build_latest_report(
        report_directory=os.path.join(
            SITE_DIR,
            "epd",
            "changes",
        ),
        filename_prefix="monthly_report_",
    )

    build_latest_report(
        report_directory=os.path.join(
            SITE_DIR,
            "scmd",
            "changes",
        ),
        filename_prefix="monthly_report_scmd_",
    )

    build_latest_report(
        report_directory=os.path.join(
            SITE_DIR,
            "epd",
            "tests",
        ),
        filename_prefix="monthly_test_report_",
    )


def build_site():
    """Build the complete static website."""

    if os.path.exists(SITE_DIR):
        shutil.rmtree(SITE_DIR)

    os.makedirs(SITE_DIR)

    # Copy static assets.
    copy_directory_contents(
        ASSETS_DIR,
        os.path.join(
            SITE_DIR,
            "assets",
        ),
    )

    # Build EPD and SCMD reports from stored CSV data.
    build_epd_reports()
    build_scmd_reports()

    # Testing remains based on existing HTML for now.
    copy_testing_reports()

    # Build navigation pages.
    build_index_page()
    build_report_list_pages()

    # Build stable latest-report links.
    build_latest_reports()

    print(
        f"Site built in {SITE_DIR}"
    )


if __name__ == "__main__":
    build_site()
import argparse
import os

import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

template_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR)
)

RAW_GITHUB_BASE = (
    "https://raw.githubusercontent.com/"
    "ebmdatalab/openprescribing-data-change-monitor/main/assets/"
)

MEASURE_BASE_URL = (
    "https://github.com/ebmdatalab/openprescribing/"
    "tree/main/openprescribing/measures/definitions"
)


def get_date_from_filename(filename):
    """Extract YYYY-MM from a report filename."""
    return filename.rsplit("_", 1)[-1].replace(".html", "")


def read_html(path):
    """Read an existing HTML report."""
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def write_html(path, html):
    """Write migrated HTML."""
    with open(path, "w", encoding="utf-8") as file:
        file.write(html)


def get_january_alert(soup):
    """
    Extract the January warning from an existing report.

    Returns an HTML string suitable for |safe in the new template.
    """
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        if "January" in text and "BNF structure" in text:
            return str(paragraph)

    return ""


def extract_tables(soup, expected_count):
    """Extract report tables as raw HTML."""
    tables = soup.find_all("table")

    if len(tables) < expected_count:
        raise ValueError(
            f"Expected at least {expected_count} tables, "
            f"but found {len(tables)}."
        )

    return [
        str(table)
        for table in tables[:expected_count]
    ]


def migrate_epd_report(source_path, apply_changes=False):
    """Migrate one EPD monthly report."""

    filename = os.path.basename(source_path)
    date = get_date_from_filename(filename)

    html = read_html(source_path)
    soup = BeautifulSoup(html, "html.parser")

    tables = extract_tables(
        soup,
        expected_count=3,
    )

    january_alert = get_january_alert(soup)

    template = template_env.get_template(
        "monthly_report_epd.html"
    )

    rendered = template.render(
        date=date,
        logo_url=f"{RAW_GITHUB_BASE}op_logo.png",
        stylesheet_url=f"{RAW_GITHUB_BASE}report.css",
        reports_index_url="index.html",
        january_alert=january_alert,
        chemical_substances=tables[0],
        bnf_codes=tables[1],
        bnf_descriptions=tables[2],
    )

    if apply_changes:
        write_html(
            source_path,
            rendered,
        )

    return rendered


def migrate_scmd_report(source_path, apply_changes=False):
    """Migrate one SCMD monthly report."""

    filename = os.path.basename(source_path)
    date = get_date_from_filename(filename)

    html = read_html(source_path)
    soup = BeautifulSoup(html, "html.parser")

    tables = extract_tables(
        soup,
        expected_count=2,
    )

    template = template_env.get_template(
        "monthly_report_scmd.html"
    )

    rendered = template.render(
        date=date,
        logo_url=f"{RAW_GITHUB_BASE}oph_logo.png",
        stylesheet_url=f"{RAW_GITHUB_BASE}report.css",
        reports_index_url="index.html",
        vtms=tables[0],
        vmps=tables[1],
    )

    if apply_changes:
        write_html(
            source_path,
            rendered,
        )

    return rendered


def get_linked_filename(link):
    """Get the final filename from a measure link."""
    href = link.get("href", "")

    if not href:
        return None

    return href.rstrip("/").split("/")[-1]


def migrate_testing_report(source_path, apply_changes=False):
    """Migrate one EPD testing report."""

    filename = os.path.basename(source_path)
    date = get_date_from_filename(filename)

    html = read_html(source_path)
    soup = BeautifulSoup(html, "html.parser")

    january_alert = get_january_alert(soup)

    triggered_tests = []
    passed_tests = []
    testing_false = []
    testing_none = []

    body = soup.find("body")

    if body is None:
        raise ValueError(
            f"No <body> found in {source_path}"
        )

    # Find the main testing headings.
    measures_heading = None
    passed_heading = None
    other_heading = None

    for heading in body.find_all(["h2", "h3"]):
        text = heading.get_text(" ", strip=True)

        if text == "Measures to check:":
            measures_heading = heading

        elif text == "Tests passed:":
            passed_heading = heading

        elif text == "Other measures":
            other_heading = heading

    # ---------------------------------------------------------
    # Triggered tests
    # ---------------------------------------------------------

    if measures_heading is not None:
        current = measures_heading.find_next_sibling()

        while current is not None:
            if current == passed_heading:
                break

            if current.name == "h2":
                break

            if current.name == "h3":
                title_link = current.find("a")

                if title_link is not None:
                    title = title_link.get_text(
                        " ",
                        strip=True,
                    )

                    comments = ""

                    next_element = current.find_next_sibling()

                    if (
                        next_element is not None
                        and next_element.name == "p"
                    ):
                        comments = next_element.get_text(
                            " ",
                            strip=True,
                        )
                        next_element = next_element.find_next_sibling()

                    table = ""

                    if (
                        next_element is not None
                        and next_element.name == "table"
                    ):
                        table = str(next_element)

                    triggered_tests.append({
                        "title": title,
                        "comments": comments,
                        "table": table,
                    })

            current = current.find_next_sibling()

    # ---------------------------------------------------------
    # Passed tests
    # ---------------------------------------------------------

    if passed_heading is not None:
        current = passed_heading.find_next_sibling()

        while current is not None:
            if current == other_heading:
                break

            if current.name == "h2":
                break

            if current.name == "p":
                link = current.find("a")

                if link is not None:
                    title = link.get_text(
                        " ",
                        strip=True,
                    )

                    passed_tests.append({
                        "title": title,
                    })

            current = current.find_next_sibling()

    # ---------------------------------------------------------
    # Other measures
    # ---------------------------------------------------------

    if other_heading is not None:
        current = other_heading.find_next_sibling()

        current_section = None

        while current is not None:

            if current.name == "h3":
                heading_text = current.get_text(
                    " ",
                    strip=True,
                )

                if heading_text == "Measures with testing disabled":
                    current_section = "testing_false"

                elif heading_text == "Measures without testing information":
                    current_section = "testing_none"

            elif current.name == "p":
                link = current.find("a")

                if link is not None:
                    filename_value = get_linked_filename(
                        link
                    )

                    if filename_value:
                        item = {
                            "filename": filename_value,
                        }

                        if current_section == "testing_false":
                            testing_false.append(item)

                        elif current_section == "testing_none":
                            testing_none.append(item)

            current = current.find_next_sibling()

    template = template_env.get_template(
        "monthly_report_epd_tests.html"
    )

    rendered = template.render(
        date=date,
        logo_url=f"{RAW_GITHUB_BASE}op_logo.png",
        stylesheet_url=f"{RAW_GITHUB_BASE}report.css",
        reports_index_url="index.html",
        january_alert=january_alert,
        measure_base_url=MEASURE_BASE_URL,
        triggered_tests=triggered_tests,
        passed_tests=passed_tests,
        testing_false=testing_false,
        testing_none=testing_none,
    )

    if apply_changes:
        write_html(
            source_path,
            rendered,
        )

    return rendered


def get_report_files(directory, prefix):
    """Return dated HTML reports for a directory."""
    return sorted(
        [
            os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if (
                filename.startswith(prefix)
                and filename.endswith(".html")
                and filename != "latest.html"
            )
        ]
    )


def migrate_directory(
    directory,
    prefix,
    migrate_function,
    apply_changes,
):
    """Migrate all reports of a particular type."""

    report_files = get_report_files(
        directory,
        prefix,
    )

    print()
    print(
        f"{len(report_files)} reports found in {directory}"
    )

    for source_path in report_files:
        filename = os.path.basename(source_path)

        try:
            migrate_function(
                source_path,
                apply_changes=apply_changes,
            )

            if apply_changes:
                print(f"Migrated: {filename}")
            else:
                print(f"Checked:   {filename}")

        except Exception as exc:
            print(
                f"ERROR: {filename}: {exc}"
            )


def migrate_all(apply_changes=False):
    """Migrate EPD, SCMD and testing reports."""

    epd_directory = os.path.join(
        REPORTS_DIR,
        "epd",
        "changes",
    )

    scmd_directory = os.path.join(
        REPORTS_DIR,
        "scmd",
        "changes",
    )

    tests_directory = os.path.join(
        REPORTS_DIR,
        "epd",
        "tests",
    )

    migrate_directory(
        epd_directory,
        "monthly_report_",
        migrate_epd_report,
        apply_changes,
    )

    migrate_directory(
        scmd_directory,
        "monthly_report_scmd_",
        migrate_scmd_report,
        apply_changes,
    )

    migrate_directory(
        tests_directory,
        "monthly_test_report_",
        migrate_testing_report,
        apply_changes,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Migrate existing OpenPrescribing HTML reports "
            "to the new Jinja templates."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually overwrite existing reports. "
            "Without this flag the script only checks them."
        ),
    )

    args = parser.parse_args()

    if args.apply:
        print(
            "MIGRATION MODE: existing reports will be overwritten."
        )
    else:
        print(
            "DRY RUN: no reports will be changed."
        )

    migrate_all(
        apply_changes=args.apply
    )


if __name__ == "__main__":
    main()
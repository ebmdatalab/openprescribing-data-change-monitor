import argparse
import os

from bs4 import BeautifulSoup
import pandas as pd


ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
DATA_DIR = os.path.join(ROOT_DIR, "data")


def get_date_from_filename(filename):
    return filename.rsplit("_", 1)[-1].replace(".html", "")


def extract_tables(path):
    """Return all HTML tables in a report as DataFrames."""
    return pd.read_html(path)


def extract_epd_report(source_path, output_dir):
    """Extract the three EPD change-report tables."""

    tables = extract_tables(source_path)

    if len(tables) < 3:
        raise ValueError(
            f"Expected at least 3 tables in {source_path}, "
            f"found {len(tables)}"
        )

    os.makedirs(output_dir, exist_ok=True)

    tables[0].to_csv(
        os.path.join(output_dir, "chemical_substances.csv"),
        index=False,
    )

    tables[1].to_csv(
        os.path.join(output_dir, "bnf_codes.csv"),
        index=False,
    )

    tables[2].to_csv(
        os.path.join(output_dir, "bnf_descriptions.csv"),
        index=False,
    )


def extract_scmd_report(source_path, output_dir):
    """Extract the two SCMD change-report tables."""

    tables = extract_tables(source_path)

    if len(tables) < 2:
        raise ValueError(
            f"Expected at least 2 tables in {source_path}, "
            f"found {len(tables)}"
        )

    os.makedirs(output_dir, exist_ok=True)

    tables[0].to_csv(
        os.path.join(output_dir, "vtms.csv"),
        index=False,
    )

    tables[1].to_csv(
        os.path.join(output_dir, "vmps.csv"),
        index=False,
    )


def extract_all_epd_reports():
    source_dir = os.path.join(
        REPORTS_DIR,
        "epd",
        "changes",
    )

    if not os.path.isdir(source_dir):
        print(f"Directory not found: {source_dir}")
        return

    report_files = sorted(
        filename
        for filename in os.listdir(source_dir)
        if (
            filename.startswith("monthly_report_")
            and filename.endswith(".html")
        )
    )

    print(f"Found {len(report_files)} EPD reports.")

    for filename in report_files:
        source_path = os.path.join(
            source_dir,
            filename,
        )

        date = get_date_from_filename(filename)

        output_dir = os.path.join(
            DATA_DIR,
            "epd",
            "changes",
            date,
        )

        extract_epd_report(
            source_path,
            output_dir,
        )

        print(f"Extracted EPD {date}")


def extract_all_scmd_reports():
    source_dir = os.path.join(
        REPORTS_DIR,
        "scmd",
        "changes",
    )

    if not os.path.isdir(source_dir):
        print(f"Directory not found: {source_dir}")
        return

    report_files = sorted(
        filename
        for filename in os.listdir(source_dir)
        if (
            filename.startswith("monthly_report_scmd_")
            and filename.endswith(".html")
        )
    )

    print(f"Found {len(report_files)} SCMD reports.")

    for filename in report_files:
        source_path = os.path.join(
            source_dir,
            filename,
        )

        date = get_date_from_filename(filename)

        output_dir = os.path.join(
            DATA_DIR,
            "scmd",
            "changes",
            date,
        )

        extract_scmd_report(
            source_path,
            output_dir,
        )

        print(f"Extracted SCMD {date}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract report tables into CSV files."
    )

    parser.add_argument(
        "--dataset",
        choices=["epd", "scmd", "all"],
        default="all",
        help="Dataset to extract.",
    )

    args = parser.parse_args()

    if args.dataset in {"epd", "all"}:
        extract_all_epd_reports()

    if args.dataset in {"scmd", "all"}:
        extract_all_scmd_reports()


if __name__ == "__main__":
    main()
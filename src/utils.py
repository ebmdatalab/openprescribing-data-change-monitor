import pandas as pd
import os
import re

from jinja2 import Environment, FileSystemLoader

# Set up Jinja templates
template_env = Environment(
    loader=FileSystemLoader("templates")
)

# tokeniser for arbitrary tails (letters, digits, other)
_token_re = re.compile(r'\d+|[A-Za-z]+|[^A-Za-z0-9]+')

def _alphanum_key(s):
    """Return tuple key for mixed alphanumeric string s."""
    parts = _token_re.findall(s or '')
    key = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))      # numeric run -> compare numerically
        elif p.isalpha():
            key.append((1, p.upper()))   # letter run -> compare lexicographically (case normalised)
        else:
            key.append((2, p))           # punctuation/other -> lowest precedence among non-numeric/alpha
    return tuple(key)

class CompareLatest:
    def __init__(self, df_existing, df_latest, exclude_chapters=[]):
        self.df_existing = df_existing
        self.df_latest = df_latest
        self.exclude_chapters = exclude_chapters
        self.new_chem_subs = None
        self.new_bnf_codes = None
        self.new_bnf_descriptions = None
        if self.exclude_chapters:
            self.df_existing = self.exclude_these_chapters(self.df_existing, self.exclude_chapters)
            self.df_latest = self.exclude_these_chapters(self.df_latest, self.exclude_chapters)
        self.find_bnf_code_only_in_latest()
        self.find_bnf_description_only_in_latest()
        self.find_chemical_substance_bnf_descr_only_in_latest()
        self.new_desc_only = self.find_unique_rows(self.new_bnf_descriptions, self.new_bnf_codes)

    def find_bnf_code_only_in_latest(self):
        latest_codes = set(self.df_latest['BNF_CODE'])
        existing_codes = set(self.df_existing['BNF_CODE'])
        unique_codes = latest_codes - existing_codes

        result = self.df_latest[self.df_latest['BNF_CODE'].isin(unique_codes)]
        self.new_bnf_codes = result

    def find_bnf_description_only_in_latest(self):
        latest_descriptions = set(self.df_latest['BNF_DESCRIPTION'])
        existing_descriptions = set(self.df_existing['BNF_DESCRIPTION'])
        unique_descriptions = latest_descriptions - existing_descriptions

        result = self.df_latest[self.df_latest['BNF_DESCRIPTION'].isin(unique_descriptions)]
        self.new_bnf_descriptions = result

    def find_chemical_substance_bnf_descr_only_in_latest(self):
        latest_substances = set(self.df_latest['CHEMICAL_SUBSTANCE_BNF_DESCR'])
        existing_substances = set(self.df_existing['CHEMICAL_SUBSTANCE_BNF_DESCR'])
        unique_substances = latest_substances - existing_substances

        result = self.df_latest[self.df_latest['CHEMICAL_SUBSTANCE_BNF_DESCR'].isin(unique_substances)]
        self.new_chem_subs = result

    @staticmethod
    def exclude_these_chapters(df, codes):
        # Separate codes starting with '~' and others
        exclude_codes = [code for code in codes if not code.startswith('~')]
        except_codes = [code[1:] for code in codes if code.startswith('~')]

        # Copy the DataFrame to avoid modifying the original
        df = df.copy()

        # Filter out rows based on the conditions
        condition_exclude_2 = df['BNF_CODE'].str[:2].isin(exclude_codes)
        condition_exclude_4 = df['BNF_CODE'].str[:4].isin(exclude_codes)
        condition_except = df['BNF_CODE'].str[:4].isin(except_codes)

        # Exclude rows meeting the exclude condition but not the except condition
        df = df[~(condition_exclude_2 | condition_exclude_4) | condition_except]

        # Reset the index of the resulting DataFrame
        df = df.reset_index(drop=True)

        return df

    @staticmethod
    def sort_by_bnf_code(df):
        """
        Hybrid sort for BNF / product codes.

        Key logic:
        1) If the code has at least 6 leading digits, interpret the first 6 as:
            chapter (2 digits), section (2 digits), paragraph (2 digits).
            The remainder (if any) is tokenised with _alphanum_key.
            Key: (0, chapter:int, section:int, paragraph:int, remainder_key)
        2) Else if the code is entirely digits, treat it as a product id and sort numerically:
            Key: (1, int(code))
        3) Otherwise treat as general alphanumeric and use _alphanum_key:
            Key: (2, alphanum_key(code))
        This preserves the BNF hierarchy while correctly ordering numeric product codes and other strings.
        """
        df = df.copy()

        cache = {}

        def make_key(code):
            s = '' if code is None else str(code)
            if s in cache:
                return cache[s]

            # attempt: first 6 chars digits -> BNF hierarchy
            prefix6 = s[:6]
            if len(prefix6) == 6 and prefix6.isdigit():
                chap = int(prefix6[:2])
                sect = int(prefix6[2:4])
                para = int(prefix6[4:6])
                tail = s[6:]
                tail_key = _alphanum_key(tail)
                key = (0, chap, sect, para, tail_key)
                cache[s] = key
                return key

            # numeric-only long product codes (e.g. 20033000572)
            if s.isdigit():
                key = (1, int(s))
                cache[s] = key
                return key

            # fallback: general alphanumeric
            key = (2, _alphanum_key(s))
            cache[s] = key
            return key

        df['_sort_key'] = df['BNF_CODE'].map(make_key)

        # stable sort to preserve order within equal keys
        df = df.sort_values(by='_sort_key', kind='mergesort').drop(columns=['_sort_key']).reset_index(drop=True)
        return df
    
    @staticmethod
    def find_unique_rows(df1, df2):
        # Merge the two dataframes with indicator to identify the source of each row
        merged_df = df1.merge(df2, how='outer', indicator=True)

        # Select the rows that are only in one of the dataframes
        unique_rows = merged_df[merged_df['_merge'] != 'both']

        # Drop the indicator column before returning
        unique_rows = unique_rows.drop(columns=['_merge'])

        return unique_rows
      
    def return_new_chem_subs(self):
        return self.sort_by_bnf_code(self.new_chem_subs)
    
    def return_new_bnf_codes(self):
        return self.sort_by_bnf_code(self.new_bnf_codes)
    
    def return_new_bnf_descriptions(self):
        return self.sort_by_bnf_code(self.new_bnf_descriptions)
    
    def return_new_desc_only(self):
        return self.sort_by_bnf_code(self.new_desc_only)

class CompareLatestSCMD:
    def __init__(self, df_existing, df_latest):
        self.df_existing = df_existing
        self.df_latest = df_latest
        self.new_vtms = None
        self.new_vmps = None
        self.find_vmp_only_in_latest()
        self.find_vtm_only_in_latest()

    def find_vmp_only_in_latest(self):
        latest = set(self.df_latest['vmp_snomed_code'])
        existing = set(self.df_existing['vmp_snomed_code'])
        unique = latest - existing
        self.new_vmps = self._sort(self.df_latest[self.df_latest['vmp_snomed_code'].isin(unique)])

    def find_vtm_only_in_latest(self):
        latest = set(self.df_latest['vtm_id'].dropna())
        existing = set(self.df_existing['vtm_id'].dropna())
        unique = latest - existing
        self.new_vtms = self._sort(self.df_latest[self.df_latest['vtm_id'].isin(unique)])

    @staticmethod
    def _sort(df):
        return df.sort_values(
            ['vtm_nm', 'vmp_product_name'],
            na_position='last'
        ).reset_index(drop=True)

    def return_new_vmps(self):
        return self.new_vmps

    def return_new_vtms(self):
        return self.new_vtms

def write_monthly_report_html(chem_subs, bnf_codes, bnf_descriptions, date):
    reports_dir = os.path.join(os.getcwd(), "reports", "epd", "changes")
    os.makedirs(reports_dir, exist_ok=True)

    # Create an alert if January data to explain BNF structure changes
    if date[-2:] == '01':
        jan_alert = (
            f'<p><b>Please note:</b> January data often includes a larger number '
            f'of "changes" as BNF structure changes are generally made in January '
            f'data - <a href="https://www.nhsbsa.nhs.uk/bnf-code-changes-january-{date[:4]}">'
            f'more information here</a></p>'
        )
    else:
        jan_alert = ''

    # Load the EPD report template
    template = template_env.get_template("monthly_report_epd.html")

    # Render the template
    report = template.render(
        date=date,
        logo_url="https://raw.githubusercontent.com/ebmdatalab/openprescribing-data-change-monitor/main/assets/op_logo.png",
        stylesheet_url=(
            "https://raw.githubusercontent.com/"
            "ebmdatalab/openprescribing-data-change-monitor/main/assets/report.css"
        ),
        reports_index_url="index.html",
        january_alert=jan_alert,
        chemical_substances=chem_subs.to_html(
            index=False,
            classes="table"
        ),
        bnf_codes=bnf_codes.to_html(
            index=False,
            classes="table"
        ),
        bnf_descriptions=bnf_descriptions.to_html(
            index=False,
            classes="table"
        ),
    )

    # Write the rendered report
    output_path = os.path.join(
        reports_dir,
        f"monthly_report_{date}.html"
    )

    with open(output_path, "w") as file:
        file.write(report)

    print(f"Report written to {output_path}")

def generate_list_reports_html():
    reports_dir = os.path.join(os.getcwd(), "reports", "epd", "changes")
    os.makedirs(reports_dir, exist_ok=True)

    # Get all HTML report files, excluding the index pages and test reports
    html_files = [
        f
        for f in os.listdir(reports_dir)
        if (
            f.endswith(".html")
            and f != "list_reports.html"
            and f != "list_test_reports.html"
            and not f.startswith("monthly_test_report")
        )
    ]

    # Extract date from filename for sorting
    def extract_date(filename):
        date_part = filename.split("_")[-1].replace(".html", "")
        return date_part

    # Sort reports chronologically
    html_files = sorted(html_files, key=extract_date)

    # Build data for the template
    reports = []

    for html_file in html_files:
        date_part = os.path.splitext(html_file)[0].split("_")[-1]
        title = pd.to_datetime(date_part).strftime("%B %Y")

        reports.append({
            "title": title,
            "url": html_file,
        })

    # Load the template
    template = template_env.get_template("report_list.html")

    # Render the template
    html_content = template.render(
        title="English Prescribing Data - Monthly New Items Reports",
        logo_url="https://raw.githubusercontent.com/ebmdatalab/openprescribing-data-change-monitor/main/assets/op_logo.png",
        logo_alt="OpenPrescribing logo",
        stylesheet_url=(
            "https://raw.githubusercontent.com/"
            "ebmdatalab/openprescribing-data-change-monitor/main/assets/report.css"
        ),
        reports=reports,
    )

    # Write the index page
    output_path = os.path.join(
        reports_dir,
        "list_reports.html"
    )

    with open(output_path, "w") as file:
        file.write(html_content)

def write_monthly_report_html_scmd(vtms, vmps, date):
    reports_dir = os.path.join(os.getcwd(), "reports", "scmd", "changes")
    os.makedirs(reports_dir, exist_ok=True)

    # Load the SCMD report template
    template = template_env.get_template("monthly_report_scmd.html")

    # Render the template
    report = template.render(
        date=date,
        logo_url="https://raw.githubusercontent.com/ebmdatalab/openprescribing-data-change-monitor/main/assets/oph_logo.png",
        stylesheet_url=(
            "https://raw.githubusercontent.com/"
            "ebmdatalab/openprescribing-data-change-monitor/main/assets/report.css"
        ),
        reports_index_url="index.html",
        vtms=vtms.to_html(
            index=False,
            classes="table"
        ),
        vmps=vmps.to_html(
            index=False,
            classes="table"
        ),
    )

    # Write the rendered report
    output_path = os.path.join(
        reports_dir,
        f"monthly_report_scmd_{date}.html"
    )

    with open(output_path, "w") as file:
        file.write(report)

    print(f"Report written to {output_path}")

def generate_list_reports_html_scmd():
    reports_dir = os.path.join(os.getcwd(), "reports", "scmd", "changes")
    os.makedirs(reports_dir, exist_ok=True)

    # Get all HTML report files, excluding the index page
    html_files = [
        f
        for f in os.listdir(reports_dir)
        if (
            f.endswith(".html")
            and f != "list_reports_scmd.html"
        )
    ]

    # Extract date from filename for sorting
    def extract_date(filename):
        date_part = filename.split("_")[-1].replace(".html", "")
        return date_part

    # Sort reports chronologically
    html_files = sorted(html_files, key=extract_date)

    # Build data for the template
    reports = []

    for html_file in html_files:
        date_part = os.path.splitext(html_file)[0].split("_")[-1]
        title = pd.to_datetime(date_part).strftime("%B %Y")

        reports.append({
            "title": title,
            "url": html_file,
        })

    # Load the template
    template = template_env.get_template("report_list.html")

    # Render the template
    html_content = template.render(
        title="Secondary Care Medicines Data - Monthly New Items Reports",
        logo_url="https://raw.githubusercontent.com/ebmdatalab/openprescribing-data-change-monitor/main/assets/oph_logo.png",
        logo_alt="OpenPrescribing Hospitals logo",
        stylesheet_url=(
            "https://raw.githubusercontent.com/"
            "ebmdatalab/openprescribing-data-change-monitor/main/assets/report.css"
        ),
        reports=reports,
    )

    # Write the index page
    output_path = os.path.join(
        reports_dir,
        "list_reports_scmd.html"
    )

    with open(output_path, "w") as file:
        file.write(html_content)
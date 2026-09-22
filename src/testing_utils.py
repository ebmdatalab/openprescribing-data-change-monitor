import pandas as pd
import os
import json
import requests
from bs4 import BeautifulSoup

from jinja2 import Environment, FileSystemLoader

# Set up Jinja templates
template_env = Environment(
    loader=FileSystemLoader("templates")
)

###### READ MEASURES FILES ######
def read_json_files_in_folder(folder_path):
    # Define a list of permissible fields for testing_as
    permissible_testing_as_fields = ["numerator_bnf_codes_filter"]
    testing_true = []
    testing_false = []
    testing_none = []
    
    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            filename_without_extension = os.path.splitext(filename)[0]
            
            # Read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                # Check if 'testing_measure' exists and is True
                if data.get('testing_measure') is True:
                    try:
                        # Check if 'testing_type' is not None
                        testing_type = data.get('testing_type')
                        if testing_type is None:
                            raise ValueError(f"In the file {filename_without_extension}, 'testing_type' is not defined.")
                        
                        # Ensure 'testing_as' is one of the permissible fields or 'custom'
                        if testing_type != 'custom' and testing_type not in permissible_testing_as_fields:
                            raise ValueError(f"In the file {filename_without_extension}, 'testing_type' must be one of {permissible_testing_as_fields} or 'custom'.")
                    
                        # Prepare the result dictionary
                        result = {
                            'filename': filename_without_extension,
                            'testing_measure': data.get('testing_measure'),
                            'testing_comments': data.get('testing_comments'),
                            'testing_type': testing_type
                        }
                    
                        # Get data to test against if 'testing_type' is not 'custom'
                        if testing_type != 'custom':
                            result['testing_type_data'] = data.get(testing_type)
                            if result['testing_type_data'] is None:
                                raise ValueError(f"In the file {filename_without_extension}, data for '{testing_type}' is missing or invalid.")
                        elif testing_type == 'custom':
                            # Handle custom case with include/exclude logic
                            result['testing_include'] = data.get('testing_include')
                            result['testing_exclude'] = data.get('testing_exclude')
                    
                            if result['testing_include'] is None or result['testing_exclude'] is None:
                                raise ValueError(f"In the file {filename_without_extension}, both 'testing_include' and 'testing_exclude' must be provided when 'testing_type' is 'custom'.")
                    
                        # Append the result to the results list
                        testing_true.append(result)
                    
                    except ValueError as e:
                        # Handle the error or log it accordingly
                        print(f"Error: {e}")
                elif data.get('testing_measure') is False:
                    result = {
                        'filename': filename_without_extension,
                        'testing_measure': data.get('testing_measure')
                    }
                    testing_false.append(result)
                else:
                    result = {
                        'filename': filename_without_extension,
                        'testing_measure': None
                    }
                    testing_none.append(result)
    return testing_true, testing_false, testing_none


# GitHub URL to scrape the list of JSON files
base_url = "https://github.com/ebmdatalab/openprescribing/tree/main/openprescribing/measures/definitions"
raw_base_url = "https://raw.githubusercontent.com/ebmdatalab/openprescribing/main/openprescribing/measures/definitions/"

def get_json_files_from_github(url):
    # Send a request to get the HTML content
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all JSON file links on the page
    json_files = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.json'):  # Only select .json files
            file_name = href.split('/')[-1]
            json_files.append(file_name)
    
    return json_files

def load_json_file(file_name):
    # Construct the raw GitHub URL for the JSON file
    file_url = raw_base_url + file_name
    response = requests.get(file_url)
    
    if response.status_code == 200:
        return response.json()  # Return JSON content as a Python dict
    else:
        raise Exception(f"Failed to load JSON file {file_name}")
    
def read_json_files_in_github():
    # Define a list of permissible fields for testing_as
    permissible_testing_as_fields = ["numerator_bnf_codes_filter"]
    testing_true = []
    testing_false = []
    testing_none = []

    # Step 1: Get list of JSON files from the GitHub directory
    json_files = get_json_files_from_github(base_url)

    # Step 2: Load each JSON file and process it
    for file_name in json_files:
        try:
            filename_without_extension = os.path.splitext(file_name)[0]
            
            # Read the JSON data using the load_json_file function
            json_data = load_json_file(file_name)

            # Check if 'testing_measure' exists and is True
            if json_data.get('testing_measure') is True:
                try:
                    # Check if 'testing_type' is not None
                    testing_type = json_data.get('testing_type')
                    if testing_type is None:
                        raise ValueError(f"In the file {filename_without_extension}, 'testing_type' is not defined.")
                    
                    # Ensure 'testing_as' is one of the permissible fields or 'custom'
                    if testing_type != 'custom' and testing_type not in permissible_testing_as_fields:
                        raise ValueError(f"In the file {filename_without_extension}, 'testing_type' must be one of {permissible_testing_as_fields} or 'custom'.")
                
                    # Prepare the result dictionary
                    result = {
                        'filename': filename_without_extension,
                        'testing_measure': json_data.get('testing_measure'),
                        'testing_comments': json_data.get('testing_comments'),
                        'testing_type': testing_type
                    }
                
                    # Get data to test against if 'testing_type' is not 'custom'
                    if testing_type != 'custom':
                        result['testing_type_data'] = json_data.get(testing_type)
                        if result['testing_type_data'] is None:
                            raise ValueError(f"In the file {filename_without_extension}, data for '{testing_type}' is missing or invalid.")
                    elif testing_type == 'custom':
                        # Handle custom case with include/exclude logic
                        result['testing_include'] = json_data.get('testing_include')
                        result['testing_exclude'] = json_data.get('testing_exclude')
                
                        if result['testing_include'] is None or result['testing_exclude'] is None:
                            raise ValueError(f"In the file {filename_without_extension}, both 'testing_include' and 'testing_exclude' must be provided when 'testing_type' is 'custom'.")
                
                    # Append the result to the results list
                    testing_true.append(result)
                
                except ValueError as e:
                    # Handle specific ValueError
                    print(f"Error in file {filename_without_extension}: {e}")

        
        except Exception as e:
            # Catch all other exceptions like network issues or parsing problems
            print(f"Failed to process {file_name}: {e}")
    
    return testing_true, testing_false, testing_none

#####################################################################################################

# Convert wildcard patterns to regex patterns
def wildcard_to_regex(pattern):
    return pattern.replace('%', '.*')

# Filter the DataFrame based on include and exclude lists
def filter_include_exclude_dataframe(df, testing_include, testing_exclude):
    # Create a boolean mask for include patterns
    include_mask = pd.Series(False, index=df.index)
    for pattern in testing_include:
        regex_pattern = wildcard_to_regex(pattern)
        include_mask |= df['BNF_CODE'].str.contains(regex_pattern)

    # Create a boolean mask for exclude patterns
    exclude_mask = pd.Series(False, index=df.index)
    for pattern in testing_exclude:
        regex_pattern = wildcard_to_regex(pattern)
        exclude_mask |= df['BNF_CODE'].str.contains(regex_pattern)

    # Filter DataFrame: include and not exclude
    filtered_df = df[include_mask & ~exclude_mask]
    return filtered_df    

def filter_num_bnf_codes_dataframe(df, testing_data):
    # Using list comprehension to remove everything from ' # ' onwards
    cleaned_data = [item.split(' # ')[0] for item in testing_data]

    # Append '.*' to each item in the cleaned_data list
    cleaned_data = [item + '%' for item in cleaned_data]

    # Creating the include list by including items that don't start with '~'
    include_list = [item for item in cleaned_data if not item.startswith('~')]
    
    # Creating the exclude list by including items starting with '~' and removing the '~'
    exclude_list = [item[1:] for item in cleaned_data if item.startswith('~')]

    # Create a boolean mask for include patterns
    include_mask = pd.Series(False, index=df.index)
    for pattern in include_list:
        regex_pattern = wildcard_to_regex(pattern)
        include_mask |= df['BNF_CODE'].str.contains(regex_pattern)

    # Create a boolean mask for exclude patterns
    exclude_mask = pd.Series(False, index=df.index)
    for pattern in exclude_list:
        regex_pattern = wildcard_to_regex(pattern)
        exclude_mask |= df['BNF_CODE'].str.contains(regex_pattern)

    # Filter DataFrame: include and not exclude
    filtered_df = df[include_mask & ~exclude_mask]
    return filtered_df    

def measures_filter(df, measure_data):
    if (measure_data['testing_type'] == 'custom'):
        filtered_df = filter_include_exclude_dataframe(df, measure_data['testing_include'], measure_data['testing_exclude'])
    elif (measure_data['testing_type'] == "numerator_bnf_codes_filter"):
        filtered_df = filter_num_bnf_codes_dataframe(df, measure_data['testing_type_data'])
    else:
        print (f"Unknown testing type {measure_data['testing_type']}")

    result = {
        "title": f"{measure_data['filename']}.json",
        "comments": measure_data['testing_comments'],
        "data": filtered_df
    }

    if not filtered_df.empty:
        result["test_triggered"] = True
    else:
        result["test_triggered"] = False
    return result
    
####### HTML REPORT CREATION #######

def write_monthly_testing_report_html(
    triggered_tests,
    passed_tests,
    testing_false,
    testing_none,
    date
):
    reports_dir = os.path.join(os.getcwd(), "reports", "epd", "tests")
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

    # Prepare the triggered test data for the template
    triggered_tests_for_template = []

    for item in triggered_tests:
        df = item["data"][
            [
                "BNF_CODE",
                "BNF_DESCRIPTION",
                "CHEMICAL_SUBSTANCE_BNF_DESCR",
            ]
        ]

        triggered_tests_for_template.append({
            "title": item["title"],
            "comments": item["comments"],
            "table": df.to_html(
                index=False,
                classes="table"
            ),
        })

    # Prepare the passed test data for the template
    passed_tests_for_template = []

    for item in passed_tests:
        passed_tests_for_template.append({
            "title": item["title"],
        })

    # Prepare the disabled test data for the template
    testing_false_for_template = []

    for item in testing_false:
        testing_false_for_template.append({
            "filename": item["filename"],
        })

    # Prepare the tests without testing information
    testing_none_for_template = []

    for item in testing_none:
        testing_none_for_template.append({
            "filename": item["filename"],
        })

    # Load the Jinja template
    template = template_env.get_template("monthly_report_epd_tests.html")

    # Base URL for measure definition links
    measure_base_url = (
        "https://github.com/ebmdatalab/openprescribing/"
        "tree/main/openprescribing/measures/definitions"
    )

    # URL for the shared stylesheet
    stylesheet_url = "../../assets/report.css"

    # Render the template
    report = template.render(
        date=date,
        logo_url="../../assets/op_logo.png",
        stylesheet_url=stylesheet_url,
        reports_index_url="index.html",
        january_alert=jan_alert,
        measure_base_url=measure_base_url,
        triggered_tests=triggered_tests_for_template,
        passed_tests=passed_tests_for_template,
        testing_false=testing_false_for_template,
        testing_none=testing_none_for_template,
    )

    # Write the rendered report
    output_path = os.path.join(
        reports_dir,
        f"monthly_test_report_{date}.html"
    )

    with open(output_path, "w") as file:
        file.write(report)

    print(f"Report written to {output_path}")

def generate_list_reports_html():
    reports_dir = os.path.join(os.getcwd(), "reports", "epd", "tests")
    os.makedirs(reports_dir, exist_ok=True)

    # Get all monthly test report files
    html_files = [
        f
        for f in os.listdir(reports_dir)
        if (
            f.endswith(".html")
            and f != "list_reports.html"
            and f != "list_test_reports.html"
            and f.startswith("monthly_test_report")
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

    # Load the shared list template
    template = template_env.get_template("report_list.html")

    # Render the template
    html_content = template.render(
        title="English Prescribing Data - Monthly Test Reports",
        logo_url="../../assets/op_logo.png",
        logo_alt="OpenPrescribing logo",
        stylesheet_url="../../assets/report.css",
        reports=reports,
    )

    # Write the index page
    output_path = os.path.join(
        reports_dir,
        "list_test_reports.html"
    )

    with open(output_path, "w") as file:
        file.write(html_content)

def run_tests(bnf_codes_df, date_for):
    folder_path = os.path.join(os.getcwd(), "measures_to_test")
    testing_true, testing_false, testing_none = read_json_files_in_folder(folder_path) # Temporary line to test locally

    #testing_true, testing_false, testing_none  = read_json_files_in_github() # Uncomment this line to use GitHub files after testing locally

    # Load the CSV file into a pandas DataFrame - Remove this line to use passed variable version after testing
    #bnf_codes_df = pd.read_csv('new_bnf_codes.csv') # Temporary line to test locally - Remove this line after testing - will use passed variable version

    # Create an empty list for triggered tests
    triggered_tests = []
    passed_tests = []

    for measure_data in testing_true:
        test_result = measures_filter(bnf_codes_df, measure_data)
        if (test_result["test_triggered"]):
            triggered_tests.append(test_result)
        else:
            passed_tests.append(test_result)

    write_monthly_testing_report_html(triggered_tests, passed_tests, testing_false, testing_none, date_for)
    generate_list_reports_html()
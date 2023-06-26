# <--- api stuff --->
import os
import requests
from dotenv import load_dotenv
load_dotenv()

# <--- text processing stuff --->
import re
import markdown
import markdown2
from bs4 import BeautifulSoup

# <--- data stuff --->
import pandas as pd
import csv
from datetime import datetime

# <--- canvas stuff --->
from canvasapi import Canvas
from canvas_helpers import *

# <--- canvas credentials --->
canvas_token = os.environ.get('CANVAS_TOKEN')
canvas_instance = "https://learning.flatironschool.com"
canvas = Canvas(canvas_instance, canvas_token)
headers = {"Authorization": f"Bearer {canvas_token}"}

# <--- custom --->
from markdown_helpers import *
from git_helpers import *
from pandas_helpers import *

def build_github_df(links):
    """
    Build a DataFrame with GitHub assignment details including HTML and Markdown content.

    Args:
        links (list): List of GitHub repository links.

    Returns:
        pd.DataFrame: DataFrame with assignment details.

    Raises:
        requests.exceptions.RequestException: If an error occurs while making the API request.
    """
    columns = ["git_repo_link"]
    df = pd.DataFrame(links, columns=columns)

    html_content = []
    markdown_content = []

    for url in links:
        if isinstance(url, str):
            url = url.replace("/blob/main/README.md", "")
            url = url.replace("/blob/master/README.md", "")
            github_repo, github_username = get_github_details(url)

            # Check for curriculum branch
            github_curriculum_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo}/curriculum/README.md"
            response = requests.get(github_curriculum_url)

            if response.status_code == 200:
                html_content.append(response.text)
                markdown_content.append(markdown2.markdown(response.text))
                continue  # Move on to the next repo

            # Check for other common branches
            branches = ["master", "main", "solution"]
            for branch in branches:
                github_branch_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo}/{branch}/README.md"
                response = requests.get(github_branch_url)
                if response.status_code == 200:
                    html_content.append(response.text)
                    markdown_content.append(markdown2.markdown(response.text))
                    break  # Found a valid branch, stop checking other branches

            else:
                # No branch found, append False values
                html_content.append(False)
                markdown_content.append(False)
        else:
            html_content.append(False)
            markdown_content.append(False)

    df["html_content"] = html_content
    df["markdown_content"] = markdown_content

    return df


def get_reading_times(df:pd.DataFrame)->(pd.DataFrame):
    df["soup_raw_text"] = df["html_content"].apply(
                                        lambda x: BeautifulSoup(x, 'html.parser') if x != False else False)
    df["raw_text_blocks"] = df["soup_raw_text"].apply(
                                        lambda x: list(x.find_all(string=True)) if x != False else False)
    df["adjusted_text_blocks"] = df["raw_text_blocks"].apply(
                                        lambda x: sum([len(n.split(" ")) for n in x]) if x != False else False)
    df["text_reading_times"] = df["adjusted_text_blocks"].apply(
                                                lambda x: round((x/200), 0) if x != False else False)
    df["soup_raw_python"] = df["html_content"].apply(lambda x: list(re.findall('```python.*\n.*', x)) if x != False else False)
    df["raw_python_blocks"] = df["soup_raw_python"].apply(lambda x: len(x) if x != False else False)
    df["adjusted_python_blocks"] = df["soup_raw_python"].apply(
                                        lambda x: sum([len(n.split(" ")) for n in x]) if x != False else False)
    df["python_reading_times"] = df["adjusted_python_blocks"].apply(lambda x: round(x*2/200, 0) + 5)
    df["total_reading_times"] = df["text_reading_times"] + df["python_reading_times"]
    df["total_reading_times"] = df["total_reading_times"].apply(lambda x: x -5 if x in [0, False] else x)
    df = df.dropna(subset=['git_repo_link'])
    df = df[df['html_content'] != False]
    return df

def generate_reading_time_reports():
    # Step 0: Check and create 'reading_time_reports' directory if it doesn't exist
    reports_dir = "reading_time_reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    input_filename = "./canvas_reports/canvas_report_202306221.csv"
    output_filename = f"reading_time_estimates_{datetime.now().strftime('%Y%m%d%H%M%S')[:12]}.csv"

    lessons = pd.read_csv(input_filename)
    links = list(lessons["git_url"])

    df = build_github_df(links)
    reading_times = get_reading_times(df)

    reading_minutes = reading_times["total_reading_times"].sum()
    reading_hours = round(reading_minutes / 60, 1)

    print(f"\nTotal Reading Time: {reading_hours} minutes\n")

    output_filepath = os.path.join(reports_dir, output_filename)
    reading_times.to_csv(output_filepath, index=False)

    print(f"Reading Times saved to {output_filepath}")
    
    return output_filepath
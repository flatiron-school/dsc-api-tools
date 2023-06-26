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

# <--- course info --->
courses = [6933, 6679, 6680, 6681, 6682]
courses = courses[:1]

# <--- github credentials --->
owner = "learn-co-curriculum"
repo_name = "dsc-mathematical-notation"
git_token = os.environ.get('GITHUB_TOKEN')


if __name__ == "__main__":
    # Step 0: Check and create 'canvas_reports' directory if it doesn't exist
    reports_dir = "canvas_reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    # Step 1: Retrieve course content
    test_df = get_course_content(courses)

    # Step 2: Process repository URLs
    repo_urls = test_df["git_url"]
    master, main, branches, updates = process_repo_urls(repo_urls, owner, repo_name, git_token)

    # Step 3: Assign processed data to DataFrame columns
    test_df["git_master_branch_dot_canvas"] = master
    test_df["git_main_branch_dot_canvas"] = main
    test_df["git_repo_all_branches"] = branches
    test_df["git_repo_all_branches_updates"] = updates

    # Step 4: Extract values from nested dictionaries in a DataFrame column
    test_df = extract_dict_values(test_df, "git_repo_all_branches_updates")

    # Step 5: Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    timestamp_short = timestamp[:9]

    # Step 6: Save DataFrame to CSV file
    filename = f"canvas_report_{timestamp_short}.csv"
    filepath = os.path.join(reports_dir, filename)
    test_df.to_csv(filepath, index=False)

    print(f"CSV report '{filename}' saved successfully.")
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
from typing import List, Optional, Dict, Tuple

# <--- canvas stuff --->
from canvasapi import Canvas

# <--- canvas credentials --->
canvas_token = os.environ.get('CANVAS_TOKEN')
canvas_instance = "https://learning.flatironschool.com"
canvas = Canvas(canvas_instance, canvas_token)
headers = {"Authorization": f"Bearer {canvas_token}"}

# <--- custom --->
from src.markdown_helpers import *
from src.git_helpers import *
from src.pandas_helpers import *


def generate_canvas_report(courses: pd.DataFrame, owner: str, repo_name: str, git_token: str) -> None:
    """
    Generate a Canvas report and save it as a CSV file.

    Args:
        courses (pd.DataFrame): DataFrame containing course data.
        owner (str): Owner of the repository.
        repo_name (str): Name of the repository.
        git_token (str): GitHub API token for authentication.

    Returns:
        None
    """
    # Step 0: Check and create 'canvas_reports' directory if it doesn't exist
    reports_dir = "canvas_reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    # Step 1: Retrieve course content
    df = get_course_content(courses)

    # Step 2: Process repository URLs
    repo_urls = df["git_url"]
    master, main, branches, updates = process_repo_urls(repo_urls, owner, git_token)

    # Step 3: Assign processed data to DataFrame columns
    df["git_master_branch_dot_canvas"] = master
    df["git_main_branch_dot_canvas"] = main
#     df["git_repo_all_branches"] = branches
    df["git_repo_all_branches_updates"] = updates

    # Step 4: Extract values from nested dictionaries in a DataFrame column
    df = extract_dict_values(df, "git_repo_all_branches_updates")

    # Step 5: Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    timestamp_short = timestamp[:9]

    # Step 6: Save DataFrame to CSV file
    filename = f"canvas_report_{timestamp_short}.csv"
    filepath = os.path.join(reports_dir, filename)
    df.to_csv(filepath, index=False)

    print(f"CSV report '{filename}' saved successfully.")
    return filepath


def get_course_content(courses: list) -> pd.DataFrame:
    """
    Retrieves course content from Canvas API and returns a DataFrame.

    Args:
        courses (list): A list of course numbers.

    Returns:
        pd.DataFrame: A DataFrame containing course content information.
    """
    # Initialize lists to store data
    page_ids, repo_urls, updated_at = [], [], []
    page_titles, page_urls = [], []
    course_numbers, phases, canvas_types = [], [], []

    for n, course_number in enumerate(courses):
        # Get course object from Canvas API
        course = canvas.get_course(course_number)
        
        # Retrieve pages from the course
        pages = course.get_pages()
        page_count = len([p for p in pages])
        print(f"[*] Retrieving {(page_count)} pages from Course #{course_number}")
        for page in pages:
            p = course.get_page(page.page_id)
            
            # Store page data
            phases.append(n)
            course_numbers.append(course_number)
            canvas_types.append("page")
            updated_at.append(p.updated_at)
            page_ids.append(p.page_id)
            page_titles.append(p.title)
            page_urls.append(p.url)
            repo_urls.append(get_git_repo_url(str(p.body)))

        # Retrieve assignments from the course
        assignments = course.get_assignments()
        assign_count = len([a for a in assignments])
        print(f"[*] Retrieving {(assign_count)} assignments from Course #{course_number}")
        for assignment in assignments:
            a = course.get_assignment(assignment.id)
            
            # Store assignment data
            phases.append(n)
            course_numbers.append(course_number)
            canvas_types.append("assignment")
            updated_at.append(a.updated_at)
            page_ids.append(a.id)
            page_titles.append(a.name)
            page_urls.append(False)
            repo_urls.append(get_git_repo_url(str(a.description)))

    # Create a list of data for the DataFrame
    canvas_data = [phases, course_numbers, page_ids, page_titles, page_urls, updated_at, repo_urls]

    # Define column names for the DataFrame
    cols = ["phase", "course_number", "canvas_page_id", "canvas_page_title",
            "canvas_page_url", "canvas_updated_at", "git_url"]

    # Create an empty DataFrame with the defined columns
    canvas_page_df = pd.DataFrame(columns=cols)

    # Assign data to DataFrame columns
    for n, col in enumerate(cols):
        canvas_page_df[col] = canvas_data[n]

    return canvas_page_df


def process_repo_urls(repo_urls: List[Optional[str]], owner: str, git_token: str) -> Tuple[List[bool], List[bool], List[List[str]], List[Dict[str, List[str]]]]:
    """
    Process repository URLs to check for dot canvas, retrieve branches, and branch updates.

    Args:
        repo_urls (List[Optional[str]]): List of repository URLs.
        owner (str): Owner of the repository.
        git_token (str): Git token for authentication.

    Returns:
        Tuple[List[bool], List[bool], List[List[str]], List[Dict[str, List[str]]]]: Tuple containing:
            - List of master branch canvas checks.
            - List of main branch canvas checks.
            - List of branches in each repository.
            - List of branch updates for each repository.
    """
    master_branch_canvas_checks = []
    main_branch_canvas_checks = []
    branches_in_repo = []
    branch_updates = []

    for url in repo_urls:
        if url is not None:
            # Check for dot canvas in master branch
            master_branch_canvas_checks.append(check_for_dot_canvas(url, "master"))
            # Check for dot canvas in main branch
            main_branch_canvas_checks.append(check_for_dot_canvas(url, "main"))
        else:
            master_branch_canvas_checks.append(False)
            main_branch_canvas_checks.append(False)

           
        if url is not None:
            # Retrieve branches in the repository
            repo_name, owner = get_github_details(url)
            branches = get_branches(owner, repo_name, git_token)
            branches_in_repo.append(branches)

            # Retrieve branch updates for each branch in the repository
            
            if branches != False:
                repo_branch_update_data = {}
                for branch in branches:
                    repo_branch_update_data[branch] = get_branch_updates(owner, repo_name, branch)
                branch_updates.append(repo_branch_update_data)
                print(f"[*] {url} complete!")
            else:
                repo_branch_update_data = {False}
                branch_updates.append(repo_branch_update_data)
        else:
            repo_branch_update_data = {False}
            branch_updates.append(repo_branch_update_data)

    return master_branch_canvas_checks, main_branch_canvas_checks, branches_in_repo, branch_updates
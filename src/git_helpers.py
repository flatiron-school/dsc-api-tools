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

# <--- python stuff --->
from typing import Optional


def get_github_details(repo_link: str) -> tuple[str, str]:
    """
    Retrieve the username and repository name from a GitHub repository link.

    Args:
        repo_link (str): GitHub repository link.

    Returns:
        tuple[str, str]: Tuple containing the repository name and username/owner.
    """
    user = repo_link.replace("https://github.com/", "")
    owner = re.sub("/.*$", "", user)
    repo_name = re.sub(".*/", "", repo_link)
    return repo_name, owner


def get_branches(owner: str, repo: str, token: str) -> list:
    """
    Get a list of all branches in a repository.

    Args:
        owner (str): Owner of the repository or organization.
        repo (str): Name of the repository.
        token (str): GitHub personal access token.

    Returns:
        list: List of branch names.
    """
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{owner}/{repo}/branches'
    response = requests.get(url, headers=headers)
#     response.raise_for_status()
    results = response.json()
    if response != 200:
        return False
    else:
        return [branch["name"] for branch in results]


def get_github_readme(owner:str, repo_name:str, branch:str)->(str):
    """
    Constructs URL for the raw README of the GitHub repo supplied 
    in the `repo_name` arg. Then, submits `requests.get` to retrieve
    the text. Outputs the response text, convers from markdown to HTML.
    
    Input:
    owner (str): GitHub username for repo
    repo_name (str): Name of GitHub repo to retrieve
    
    Output:
    html_content (str): Contents of README.md, converted to HMTL
    """
    repo_url = f"{github_user}/{repo_name}/{branch}"
    readme_url = f"https://raw.githubusercontent.com/{repo_url}/README.md"
    print(readme_url)
    git_resp = requests.get(readme_url)
    html_content = git_resp.text
    markdown_content = markdown2.markdown(html_content)
    return git_resp, html_content, markdown_content


def get_git_repo_url(html: str) -> Optional[str]:
    """
    Retrieve the first url that starts with a specified string from the HTML content.

    Args:
        html (str): HTML content to search for URLs.

    Returns:
        Optional[str]: The first URL that starts with `https://github.com/`, or `None` if not found.
    """
    if html is not None and len(html) > 0:
        soup = BeautifulSoup(html, features="html.parser")
        urls = [node.get("href") for node in soup.find_all("a")]
        if len(urls) > 0 and str(urls[0]).startswith("https://github.com/"):
            print(urls[0])
            return urls[0]
        else:
            return None
    else:
        return None

import requests


def check_for_dot_canvas(repo_url: str, branch: str) -> bool:
    """
    Check if a repository and branch have a `.canvas` file.

    Args:
        repo_url (str): The URL of the repository.
        branch (str): The branch name.

    Returns:
        bool: True if the `.canvas` file is found, False otherwise.
    """
    repo_name, owner = get_github_details(repo_url)
    repository = f"{owner}/{repo_name}"
    branch_url = f"https://api.github.com/repos/{repository}/branches/{branch}"
    dot_canvas_url = f"https://raw.githubusercontent.com/{repository}/{branch}/.canvas"
    response = requests.get(dot_canvas_url)
    if response.status_code == 200:
        return True
    else:
        return False

    
def get_branch_updates(owner: str, repo_name: str, branch: str) -> str:
    """
    Retrieve the last commit date for a specific branch in a GitHub repository.

    Args:
        owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository.
        branch (str): The name of the branch.

    Returns:
        str: The last commit date for the specified branch in ISO 8601 format.

    Raises:
        requests.exceptions.RequestException: If an error occurs while making the API request.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    branch_url = f"{url}/branches/{branch}"
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(branch_url, headers=headers)
        response.raise_for_status()

        branch_data = response.json()
        last_commit_date = branch_data["commit"]["commit"]["author"]["date"]

        return last_commit_date

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Error occurred during API request: {e}")
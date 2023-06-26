# api stuff
import os
import requests

from dotenv import load_dotenv
load_dotenv()

from canvasapi import Canvas
# canvas_api_key = os.environ.get('CANVAS_TOKEN')
# canvas_instance = "https://learning.flatironschool.com"
# canvas = Canvas(canvas_instance, canvas_api_key)

# text processing stuff
import re
import markdown
import markdown2
from bs4 import BeautifulSoup

import pandas as pd

# language model stuff
# import spacy
# from spacy.pipeline import EntityRuler
# nlp = spacy.load("en_core_web_trf")
# from spacy.language import Language
# from spacy.tokens import Doc


# HTML Functions
def process_html(html: str)->(str):
    "Helper function to process HTML for quick text-extraction with BS4."
    text = str(''.join(BeautifulSoup(html, "html.parser").findAll(text=True)))
    text = re.sub("\n\n", " ", text)
    text = re.sub("\n", " ", text)
    text = text.split(" ")
    text = ' '.join(text)
    return text


def convert_lesson_text(readme_content:str)->(str, str):
    """
    Orchestrates conversion of lesson text into three types:
        - `html` -> (markdown) 
        - `text` -> (plain text string)
        - `doc` -> (spacy Doc)

    Input:
    readme_content (str): raw HTML string of lesson README page

    Output:
    html (str): 
    text (str):
    doc (Doc): 
    """
    markdown2_text = markdown2.markdown(readme_content)
    plain_text = process_html(markdown2_text)
    return markdown2_text, plain_text


## Github Functions
def extract_github_details(repo_link:str)->(str, str):
    "Helper function to quickly retrieve username and repository from repo link."
    user = repo_link.replace("https://github.com/", "")
    github_username = re.sub("/.*$", "", user)
#     print(f"user: {github_username}")

    github_repo = re.sub(".*/", "", repo_link)
    print(f"repo: {github_repo}")
    return github_repo, github_username


def get_repo_link(html: str)->(str):
    "Helper function to process HTML for quick text-extraction with BS4."
    if html != None and len(html) > 0:
        soup = BeautifulSoup(html, features='html.parser')
        links = [node.get('href') for node in soup.find_all("a")]
        if len(links) > 0 and str(links[0]).startswith('https://github.com/'):
            print(links[0])
            return links[0]
        else:
            return False
    else:
        return False


def get_github_readme(github_username:str, github_repo:str)->(str):
    """
    Constructs URL for the raw README of the GitHub repo supplied 
    in the `github_repo` arg. Then, submits `requests.get` to retrieve
    the text. Outputs the response text, convers from markdown to HTML.
    
    Input:
    github_username (str): GitHub username for repo
    github_repo (str): Name of GitHub repo to retrieve
    
    Output:
    html_content (str): Contents of README.md, converted to HMTL
    """
    # get content of README file
    github_readme_url = f"https://raw.githubusercontent.com/learn-co-curriculum/{github_repo}/master/README.md"
    print(github_readme_url)
    git_resp = requests.get(github_readme_url)
    
    # 
    if git_resp != 200:
        github_readme_url = f"https://raw.githubusercontent.com/learn-co-curriculum/{github_repo}/main/README.md"
        print(github_readme_url)
        git_resp = requests.get(github_readme_url)
        html_content = git_resp.text
        # convert the GitHub README file content to HTML
        markdown_content = markdown2.markdown(html_content)
        return git_resp, html_content, markdown_content

    else:
        html_content = git_resp.text
        # convert the GitHub README file content to HTML
        markdown_content = markdown2.markdown(html_content)
        return git_resp, html_content, markdown_content


## Canvas Functions
def get_canvas():
    """
    Helper function to quickly connect to Canvas API.
    Requires that .env file is configured with `CANVAS_TOKEN`.
    
    output:
    canvas (Canvas): canvas instance
    """
    import os
    from canvasapi import Canvas
    canvas_api_key = os.environ.get('CANVAS_TOKEN')
    canvas_instance = "https://learning.flatironschool.com"
    canvas = Canvas(canvas_instance, canvas_api_key)
    return canvas


def get_lesson_links(course_number:int)->(list):
    """
    Helper function to quickly connect to Canvas API 
    with `get_canvas()`.
    Retrieves links for pages in Canvas instance.
    
    input: 
    course_number (int): Canvas course number to retrieve
    
    output:
    links (list): links for pages in Canvas course
    """
    canvas = get_canvas()
    course = canvas.get_course(course_number)
    pages = course.get_pages()
    links = []
    for p in pages:
        links += [p.url]
    return links


def build_github_assignment_df(links):   
    # create dataframe from the lists
    columns = ["git_repo_link"]
    assignment_data = pd.DataFrame(links, columns=columns)
    
    html_content = []
    markdown_content = []
    for url in links:
        if type(url) == str:
#             url = url.replace("https://github.com/learn-co-curriculum/", "")
            url = url.replace("/blob/main/README.md", "")
            url = url.replace("/blob/master/README.md", "")

            github_repo, github_username = extract_github_details(url)
#             github_solution_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo}/solution/README.md"
            github_curriculum_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo}/curriculum/README.md"
            
#             git_resp = requests.get(github_solution_url)
#             html_content += [git_resp.text]
#             markdown_content += [markdown2.markdown(git_resp.text)]
            
            git_resp = requests.get(github_curriculum_url)
            html_content += [git_resp.text]
            markdown_content += [markdown2.markdown(git_resp.text)]
            
        else:
            html_content += [False]
            markdown_content += [False]
        
    assignment_data["html_content"] = html_content
    assignment_data["markdown_content"] = markdown_content

    return assignment_data


def get_assignment_reading_times(assignment_data:pd.DataFrame)->(pd.DataFrame):
    assignment_data["soup_raw_text"] = assignment_data["html_content"].apply(
                                        lambda x: BeautifulSoup(x, 'html.parser') if x != False else False)
    assignment_data["raw_text_blocks"] = assignment_data["soup_raw_text"].apply(
                                        lambda x: list(x.find_all(string=True)) if x != False else False)
    assignment_data["adjusted_blocks"] = assignment_data["raw_text_blocks"].apply(
                                        lambda x: sum([len(n.split(" ")) for n in x]) if x != False else False)
    assignment_data["assignment_word_reading_times"] = assignment_data["adjusted_blocks"].apply(
                                                lambda x: round((x/200), 0) if x != False else False)
    assignment_data["soup_raw_python"] = assignment_data["html_content"].apply(lambda x: list(re.findall('```python.*\n.*', x)) if x != False else False)
    assignment_data["python_blocks_count"] = assignment_data["soup_raw_python"].apply(lambda x: len(x) if x != False else False)
    assignment_data["python_words_per_block"] = assignment_data["soup_raw_python"].apply(
                                        lambda x: [len(n.split(" ")) for n in x] if x != False else False)
    assignment_data["python_total_words"] = assignment_data["python_words_per_block"].apply(
                                        lambda x: sum(x) if x != False else False)
    assignment_data["total_python_reading_times"] = assignment_data["python_total_words"].apply(lambda x: round(x*2/200, 0) + 5)

    assignment_data["total_text_reading_times"] = assignment_data["assignment_word_reading_times"] + assignment_data["total_python_reading_times"]

    assignment_data.loc[assignment_data["python_blocks_count"] == 0, "total_text_reading_times"] = assignment_data["total_text_reading_times"] - 5

    return assignment_data

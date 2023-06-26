import re
import markdown
import markdown2
from bs4 import BeautifulSoup
from bs4 import Tag


def process_html(html: str) -> str:
    """
    Helper function to process HTML for quick text extraction with BeautifulSoup.

    Args:
        html (str): HTML content to be processed.

    Returns:
        str: Processed text extracted from HTML.
    """
    text = str(''.join(BeautifulSoup(html, features="html.parser").findAll(text=True)))
    text = re.sub("\n\n", " ", text)
    text = re.sub("\n", " ", text)
    text = text.split(" ")
    text = ' '.join(text)
    return text


def convert_lesson_text(readme_content:tuple)->(str, str):
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


def extract_text_from_element(element: Tag) -> str:
    """
    Extracts text content from an HTML element.

    Args:
        element (bs4.Tag): HTML element to extract text from.

    Returns:
        str: Extracted text content.
    """
    text = ""
    if isinstance(element, Tag):
        if element.name == "h3":
            text += f"## {str(element.string)}\n\n"
        elif element.name == "h4":
            text += f"### {str(element.string)}\n\n"
        else:
            if element.name in ["p"]:
                text += str(element.string) + "\n\n"
            elif element.name in  ["em", "strong"]:
                text += f"**{str(element.string)}** \n\n"
            elif element.name == "ul":
                text += "".join([extract_text_from_element(li) for li in element.find_all("li")])
            elif element.name == "ol":
                text += "".join([extract_text_from_element(li) for li in element.find_all("li")])
            elif element.name == "li":
                if element.find("code"):
                    text += "- `" + str(element.find("code").string) + "`\n"
                else:
                    text += "- " + str(element.string) + "\n"
            elif element.name == "code":
                text += f"`{str(element.string)}`"
            else:
                element_ = str(element).replace("None", "")
                text += str(element_) + "\n\n"

        if element.next_sibling and element.next_sibling.name not in ["h3", "h4"]:
            text += extract_text_from_element(element.next_sibling)

    return text


def convert_to_markdown(title: str, html_page: str) -> str:
    """
    Converts an HTML page to Markdown format.

    Args:
        title (str): Title of the Markdown document.
        html_page (str): HTML content to be converted.

    Returns:
        str: Markdown representation of the HTML page.
    """
    markdown = f"# {title}\n\n"
    soup = BeautifulSoup(html_page, "html.parser")
    sections = soup.find_all("h3")
    for section in sections:
        cleaned_text = f"## {str(section.string)}\n\n"
        next_element = section.next_sibling
        while next_element and next_element.name != "h3":
            cleaned_text += extract_text_from_element(next_element)
            next_element = next_element.next_sibling
        markdown += cleaned_text + "\n"
    return markdown

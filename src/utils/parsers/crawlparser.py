import logging
import re

from bs4 import BeautifulSoup

from src.utils.parsers.urlparser import URLParser

logger = logging.getLogger(__name__)


class CrawlParser():
    def __init__(self, html: str) -> None:
        self._html = html
        self._soup = BeautifulSoup(html, "lxml")
        self._soup.prettify()
        for data in self._soup(['style', 'script']):
            data.decompose()
        pass

    def get_semantic_content(self):
        body = self._soup.find("body")
        if body is None:
            return None

        semantic_tags = body.find_all([
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
        ])
        joined_content = "<body>"
        for semantic_tag in semantic_tags:
            joined_content += semantic_tag.decode().replace("\n", "")
        joined_content += "</body>"
        resoup = BeautifulSoup(joined_content, "lxml")
        for data in resoup(['a']):
            data.decompose()
        return resoup.decode()

    def get_safe_hrefs(self):
        hrefs = []
        a_tags = self._soup.find_all("a", attrs={"href": re.compile(r"^(?!#).+")})
        for a_tag in a_tags:
            href = str(a_tag.attrs["href"])
            url_parser = URLParser(href)
            pretty_href = url_parser.prettify()
            if not pretty_href.startswith("http"):
                continue
            if pretty_href not in hrefs:
                hrefs.append(url_parser.prettify())
        return hrefs
    
    def get_unsafe_hrefs(self):
        hrefs = []
        a_tags = self._soup.find_all("a", attrs={"href": re.compile(r"^(?!#).+")})
        for a_tag in a_tags:
            href = str(a_tag.attrs["href"])
            if href.startswith("http"):
                continue
            if href not in hrefs:
                hrefs.append(href)
        return hrefs
    
    def get_title(self):
        title_tag = self._soup.find("title")
        if title_tag is None:
            return None
        return title_tag.text

    def get_description(self):
        description_tag = self._soup.find("meta", attrs={"name": "description_tag"})
        if description_tag is None:
            return None
        return str(description_tag.attrs["content"])

    def get_keywords(self):
        keywords_tag = self._soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag is None:
            return None
        return str(keywords_tag.attrs["content"]).replace(", ", ",")

    def get_lang(self):
        html_tag = self._soup.find("html")
        if html_tag is None:
            return None
        return str(html_tag.attrs["lang"])
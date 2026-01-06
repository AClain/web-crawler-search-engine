import logging

from bs4 import BeautifulSoup, Tag

from src.models.Link import ChangeFreq, Link
from src.utils.math import normalize_priority

logger = logging.getLogger(__name__)



class SitemapParser:
    def __init__(self, sitemap_xml: str) -> None:
        self._soup = BeautifulSoup(sitemap_xml, "xml")
        pass

    def _process_index(self, index_tag: Tag):
        url_list = []
        sitemaps = index_tag.find_all("sitemap")
        for sitemap in sitemaps:
            url = sitemap.find("loc")
            if url is not None and not url.text.endswith(".gz"):
                url_list.append(url.text)
        return url_list
    
    def _process_urlset(self, urlset_tag: Tag) -> list[Link]:
        link_list = []
        urls = urlset_tag.find_all("url")
        for url in urls:
            loc = url.find('loc')
            if loc is None:
                continue
            #? priority_tag = url.find('priority')?.text ?? 0.5
            priority_tag = url.find('priority')
            priority = 0.5
            if priority_tag is not None:
                priority = normalize_priority(float(priority_tag.text))
            changefreq_tag = url.find('changefreq')
            changefreq = ChangeFreq.MONTHLY
            if changefreq_tag is not None:
                try:
                    changefreq = ChangeFreq(changefreq_tag.text.lower())
                except Exception:
                    logger.error(f"{changefreq_tag.text} is not a valid ChangeFreq.")
            link = Link(url=loc.text, priority=priority, change_freq=changefreq)
            link_list.append(link)
        return link_list
    
    def get_indexes(self) -> list[str]:
        url_list = []
        
        indexes = self._soup.find_all("sitemapindex")
        for index in indexes:
            url_list.extend(self._process_index(index))
        return url_list

    
    def get_links(self) -> list[Link]:
        link_list= []
        urlsets = self._soup.find_all("urlset")
        for urlset in urlsets:
            link_list.extend(self._process_urlset(urlset))
        return link_list

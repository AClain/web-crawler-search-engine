import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class URLParser:
    def __init__(self, url: str) -> None:
        self._raw_url = url
        self._parsed_url = urlparse(url)
        pass

    def get_scheme(self):
        return self._parsed_url.scheme

    def get_domain(self):
        hostname = str(self._parsed_url.hostname)
        if not hostname.startswith("www") and hostname.count(".") == 1:
            hostname = f"www.{self._parsed_url.hostname}"
        return hostname

    def prettify(self):
        hostname = self.get_domain()
        final_url = f"{self._parsed_url.scheme}://{hostname}"
        path = self._parsed_url.path
        if path.endswith("/"):
            path = path[:-1]
        final_url += path
        return final_url


from random import randrange

import requests
from requests import adapters

from src.vars import HTTP_TIMEOUT, USER_AGENTS


def get_user_agent():
    return USER_AGENTS[randrange(1, len(USER_AGENTS))]

class HTTPClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': get_user_agent()
        })
        adapter = adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)

    def fetch(self, url: str):
        return self._session.get(url, timeout=HTTP_TIMEOUT)
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.Link import Link


class LinkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        pass

    def insert_one(self, link: Link):
        self._session.add(link)
        self._session.flush()
        self._session.refresh(link)

    def insert_many(self, *links: Link):
        self._session.add_all(links)
        self._session.flush()
        for link in links:
            self._session.refresh(link)

    def read_all(self):
        query = select(Link)
        links = self._session.scalars(query).all()
        return links

    def read_one(self, id: uuid.UUID):
        query = select(Link).where(Link.id == id)
        link = self._session.scalar(query)
        return link

    def find_one_by_url(self, url: str):
        query = select(Link).where(Link.url == url)
        link = self._session.scalar(query)
        return link

    def delete_one(self, link: Link):
        # TODO
        self._session.delete(link)
        self._session.flush()
        return link.id

    def delete_many(self, *links: Link):
        for link in links:
            self.delete_one(link)

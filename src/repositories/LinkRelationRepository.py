import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.LinkRelation import LinkRelation


class LinkRelationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        pass

    def insert_one(self, link_relation: LinkRelation):
        self._session.add(link_relation)
        self._session.flush()
        self._session.refresh(link_relation)

    def insert_many(self, *link_relations: LinkRelation):
        self._session.add_all(link_relations)
        self._session.flush()
        for link_relation in link_relations:
            self._session.refresh(link_relation)

    def read_all(self):
        query = select(LinkRelation)
        link_relation = self._session.scalars(query).all()
        return link_relation

    def find_one_by_relation(self, link_id: uuid.UUID, has_link_id: uuid.UUID):
        query = select(LinkRelation).where(LinkRelation.link_id == link_id).where(LinkRelation.has_link_id == has_link_id)
        link_relation = self._session.scalar(query)
        return link_relation
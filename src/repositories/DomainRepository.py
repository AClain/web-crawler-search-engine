import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.Domain import Domain


class DomainRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        pass

    def insert_one(self, domain: Domain):
        self._session.add(domain)
        self._session.flush()
        self._session.refresh(domain)

    def insert_many(self, *domains: Domain):
        self._session.add_all(domains)
        self._session.flush()
        for domain in domains:
            self._session.refresh(domain)

    def upsert_one(self, domain: Domain):
        query = (
            insert(Domain)
            .values(name=domain.name, protocol=domain.protocol)
            .on_conflict_do_nothing(index_elements=["name"])
        )

        self._session.execute(query)
        self._session.flush()

        return self.find_one_by_name(domain.name)

    def read_all(self):
        query = select(Domain)
        domains = self._session.scalars(query).all()
        return domains

    def read_one(self, id: uuid.UUID):
        query = select(Domain).where(Domain.id == id)
        domain = self._session.scalar(query)
        return domain

    def find_one_by_name(self, name: str):
        query = select(Domain).filter(Domain.name == name)
        domain = self._session.scalar(query)
        return domain

    def delete_one(self, domain: Domain):
        self._session.delete(domain)
        self._session.flush()
        return domain.id

    def delete_many(self, *domains: Domain):
        for domain in domains:
            self.delete_one(domain)

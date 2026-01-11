# Web Crawler

## Getting started

This project is written in Python and uses :

- [ruff](https://docs.astral.sh/ruff/tutorial/) for type checking
- [uv](https://docs.astral.sh/uv/getting-started/) for package management
- [PostgreSQL](https://www.postgresql.org/docs/) as its database management system
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) as its database migrations management
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) as its ORM
- [pytest](https://docs.pytest.org/en/stable/getting-started.html) for unit tests
- [BeautifulSoup4](https://beautiful-soup-4.readthedocs.io/en/latest/#quick-start) for HTML and XML parsing / scraping

### Setup workers (with docker)

- Start services

```
chmod +x ./capy.sh
./capy.sh start services
```

- Run migrations

```
uv run alembic upgrade head
```

- Start workers

```
./capy.sh start workers
```

- Stop services

```
./capy.sh stop services
```

- Stop workers

```
./capy.sh stop services
```

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

- Run migrations

```
uv run alembic upgrade head
```

- Start workers

```
chmod +x start-workers.sh
./start-workers
```

- Start workers only

```
chmod +x stop-workers.sh
./stop-workers
```

### Setup workers (without docker, will be slower)

- Start domains worker with `uv run -m src.workers.domains`

  > The domain workers will populate the sitemap queue and will dipsatch one link to the links queue

- Start sitemaps worker with `uv run -m src.workers.sitemaps`

  > The sitemap workers will populate the links queue

- Start links worker with `uv run -m src.workers.links`

  > The links workers will populate the prioritizer queue

- Start links prioritizer with `uv run -m src.workers.prioritizer`

  > The prioritizer workers will populate the router queues

- Start links router with `uv run -m src.workers.router <priority>`

  > The router workers will populate the selector queues

- Start links selector with `uv run -m src.workers.selector 1`

  > The selector workers will populate the links queue. This is where the crawling is done

- Start links selector with `uv run -m src.workers.selector 2`

  > The selector workers will populate the links queue. This is where the crawling is done

- Start links selector with `uv run -m src.workers.selector 3`

  > The selector workers will populate the links queue. This is where the crawling is done

- Start links selector with `uv run -m src.workers.selector 4`

  > The selector workers will populate the links queue. This is where the crawling is done

- Start links selector with `uv run -m src.workers.selector 5`
  > The selector workers will populate the links queue. This is where the crawling is done

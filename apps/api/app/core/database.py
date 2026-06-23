from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from app.core.config import settings


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg://")
    return url


database_url = _normalize_database_url(settings.database_url)
connection_pool = ConnectionPool(
    conninfo=database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)


@contextmanager
def db_connection() -> Iterator[Connection]:
    if connection_pool.closed:
        connection_pool.open()
    with connection_pool.connection() as connection:
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

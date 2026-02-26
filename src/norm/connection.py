from typing import Protocol
from urllib.parse import urlparse
from warnings import deprecated


class AsyncDatabase(Protocol):
    """A class representing an asynchronous database connection."""

    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...
    async def execute(self, query: str, *args, **kwargs): ...
    async def begin(self): ...
    async def commit(self): ...
    async def flush(self): ...
    async def rollback(self): ...


@deprecated()
async def connect(
    dsn: str,
    *,
    echo: bool | None = False,
) -> AsyncDatabase:
    """
    Connect to a database.

    Args:
        dsn: The Data Source Name (DSN) string that specifies
         the connection details for the database.
        echo: Enable query logging.

    Returns:
        A connection object that can be used to interact with the database.

    """
    parsed = urlparse(dsn)
    if parsed.scheme not in {'postgresql+asyncpg', 'postgresql+psycopg'}:
        raise ValueError(f'Unsupported database scheme: {parsed.scheme}')

    raise NotImplementedError(
        "The 'connect' function must be implemented by the database driver."
    )

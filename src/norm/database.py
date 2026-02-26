from typing import Any, Self

from asyncpg import Pool, create_pool

from norm.transaction import Transaction


class AsyncDatabase:
    """A class representing an asynchronous PostgreSQL database connection."""

    def __init__(
        self,
        dsn: str,
        *,
        echo: bool | None = False,
        min_connections: int = 10,
        max_connections: int = 50,
        max_inactive_connection_lifetime: int = 300,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AsyncPostgreSQLDatabase instance.

        Args:
            dsn: The Data Source Name (DSN) string that specifies
             the connection details for the database.
            echo: Enable query logging.
            min_connections: The minimum number of connections in the pool.
            max_connections: The maximum number of connections in the pool.
            max_inactive_connection_lifetime: The maximum lifetime of
             inactive connections in seconds.
            **kwargs: Additional keyword arguments
             to be passed to the asyncpg connection pool.

        """
        if not dsn.startswith("postgresql://"):
            raise ValueError("NORM only supports postgresql+asyncpg")
        self._dsn = dsn
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self._asyncpg_args = kwargs

        self._pool: Pool | None = None
        self._echo: bool | None = False

    async def connect(self) -> Self:
        """
        Establish a connection pool to the PostgreSQL database using the
         configuration provided when this AsyncDatabase instance was created.

        Returns:
            Self: The instance of AsyncDatabase with an established
            connection pool.

        Raises:
            RuntimeError: If a connection pool is already established.

        """
        if self._pool is not None:
            raise RuntimeError("Connection pool is already established.")

        self._pool = await create_pool(
            dsn=self._dsn,
            min_size=self._min_connections,
            max_size=self._max_connections,
            max_inactive_connection_lifetime=self._max_inactive_connection_lifetime,
            **self._asyncpg_args,
        )
        return self

    async def disconnect(self) -> None:
        """
        Close the connection pool to the PostgreSQL database.

        Returns:
            None

        """
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def __aenter__(self) -> Self:
        """
        Enter the asynchronous context manager.

        Returns:
            Self: The instance of AsyncDatabase with an established
             connection pool.

        """
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """
        Exit the asynchronous context manager.

        Args:
            exc_type (type[BaseException] | None): The type of the exception
             that caused the context to exit, or None if no exception occurred.
            exc_val (BaseException | None): The exception instance that caused
             the context to exit, or None if no exception occurred.
            exc_tb (Any): The traceback object associated with the exception,
             or None if no exception occurred.

        Returns:
            None

        """
        await self.disconnect()

    async def execute(self, query: str, *args: Any) -> None:
        """
        Execute a SQL query against the database.

        Args:
            query (str): The SQL query to be executed.
            *args (Any): The parameters to be passed to the SQL query.

        Returns:
            None

        Raises:
            RuntimeError: If the connection pool is not established.

        """
        if self._pool is None:
            raise RuntimeError("Connection pool is not established.")

        async with self._pool.acquire() as connection:
            await connection.execute(query, *args)

    def begin(
        self,
        *,
        isolation: str | None = None,
        readonly: bool | None = None,
        deferrable: bool | None = None,
    ) -> Transaction:
        """
        Begin a new transaction.

        Args:
            isolation (str | None): The isolation level for the transaction.
            readonly (bool | None): Whether the transaction is read-only.
            deferrable (bool | None): Whether the transaction is deferrable.

        Returns:
            Transaction: An instance of the Transaction class representing
             the new transaction.

        Raises:
            RuntimeError: If the connection pool is not established.

        """
        if self._pool is None:
            raise RuntimeError("Connection pool is not established.")

        return Transaction(
            pool=self._pool,
            isolation=isolation,
            readonly=readonly,
            deferrable=deferrable,
        )

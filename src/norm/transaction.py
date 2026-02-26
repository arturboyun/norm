from typing import Any

from asyncpg import Connection, Pool
from asyncpg.transaction import Transaction as AsyncpgTransaction


class Transaction:
    """A class representing a database transaction."""

    def __init__(
        self,
        pool: Pool,
        *,
        isolation: str | None = None,
        readonly: bool | None = None,
        deferrable: bool | None = None,
    ) -> None:
        """
        Initialize the Transaction instance.

        Args:
            pool: An instance of asyncpg.Pool representing the database connection pool.
            isolation: The isolation level for the transaction.
            readonly: Whether the transaction is read-only.
            deferrable: Whether the transaction is deferrable.

        """
        self._pool = pool
        self._connection: Connection = None
        self._tx: AsyncpgTransaction = None

        self._isolation = isolation
        self._readonly = readonly
        self._deferrable = deferrable

    async def __aenter__(self) -> Connection:
        """Enter the asynchronous context manager."""
        self._connection = await self._pool.acquire()
        self._tx = await self._connection.transaction(
            isolation=self._isolation,
            readonly=self._readonly,
            deferrable=self._deferrable,
        )
        await self._tx.start()
        return self._connection

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the asynchronous context manager."""
        try:
            if exc_type is not None:
                await self._tx.rollback()
            else:
                await self._tx.commit()
        finally:
            if self._connection is not None:
                await self._pool.release(self._connection)

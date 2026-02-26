from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from norm.database import AsyncDatabase


@pytest.mark.asyncio
class TestAsyncDatabase:
    """Unit tests for the AsyncDatabase class."""

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_database_initialization(self, mock_create_pool: AsyncMock) -> None:
        """Test the initialization of the AsyncDatabase class."""
        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )

        await db.connect()
        await db.disconnect()

        assert db._dsn == 'postgresql://user:password@localhost:5432/mydatabase'
        assert db._min_connections == 1
        assert db._max_connections == 10
        assert db._max_inactive_connection_lifetime == 300

        mock_create_pool.assert_called_once_with(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_size=1,
            max_size=10,
            max_inactive_connection_lifetime=300,
        )

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_database_context_manager(self, mock_create_pool: AsyncMock) -> None:
        """Test the context manager functionality of the AsyncDatabase class."""
        async with AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        ):
            # You can perform database operations here
            pass

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_database_execute_method(self, mock_create_pool: AsyncMock) -> None:
        """Test the execute method of the AsyncDatabase class."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()

        @asynccontextmanager
        async def acquire_cm() -> AsyncIterator[AsyncMock]:
            yield mock_conn

        mock_pool.acquire = acquire_cm
        mock_create_pool.return_value = mock_pool

        async with AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        ) as db:
            await db.execute('SELECT 1')

            mock_conn.execute.assert_awaited_once_with('SELECT 1')

    async def test_invalid_dsn(self) -> None:
        """Test that an invalid DSN raises a ValueError."""
        with pytest.raises(
            ValueError,
            match=r'NORM only supports postgresql\+asyncpg',
        ):
            AsyncDatabase(dsn='invalid_dsn')

    async def test_disconnect_without_connection(self) -> None:
        """Disconnect without a pool should not error."""
        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )

        await db.disconnect()  # Should not raise an error

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_double_connect(self, mock_create_pool: AsyncMock) -> None:
        """Test that calling connect twice raises a RuntimeError."""
        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )
        await db.connect()

        with pytest.raises(
            RuntimeError,
            match=r'Connection pool is already established.',
        ):
            await db.connect()

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_execute_without_connection(self, mock_create_pool: AsyncMock) -> None:
        """Test execute without a pool raises a RuntimeError."""
        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )

        with pytest.raises(RuntimeError, match=r'Connection pool is not established.'):
            await db.execute('SELECT 1')

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_database_transaction_management(
        self, mock_create_pool: AsyncMock
    ) -> None:
        """Test the transaction management functionality of the AsyncDatabase class."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()

        mock_pool.acquire = AsyncMock(return_value=mock_conn)

        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_conn.transaction.return_value = mock_tx

        mock_create_pool.return_value = mock_pool

        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )
        await db.connect()

        async with db.begin() as conn:
            await conn.execute('SELECT 1')

        await db.disconnect()

    async def test_begin_without_connection(self) -> None:
        """Begin without a pool raises a RuntimeError."""
        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )

        async def _use_begin() -> None:
            async with db.begin():
                pass

        with pytest.raises(RuntimeError, match=r'Connection pool is not established.'):
            await _use_begin()

    @patch('norm.database.create_pool', new_callable=AsyncMock)
    async def test_transaction_rollback_on_exception(
        self, mock_create_pool: AsyncMock
    ) -> None:
        """Test that a transaction rolls back on exception."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()

        mock_pool.acquire = AsyncMock(return_value=mock_conn)

        mock_tx = AsyncMock()
        mock_tx.start = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.rollback = AsyncMock()
        mock_conn.transaction.return_value = mock_tx

        mock_create_pool.return_value = mock_pool

        db = AsyncDatabase(
            dsn='postgresql://user:password@localhost:5432/mydatabase',
            min_connections=1,
            max_connections=10,
            max_inactive_connection_lifetime=300,
        )
        await db.connect()

        async def _run_tx() -> None:
            async with db.begin() as conn:
                await conn.execute('SELECT 1')
                raise ValueError('Test exception')

        with pytest.raises(ValueError, match=r'Test exception'):
            await _run_tx()

        await db.disconnect()

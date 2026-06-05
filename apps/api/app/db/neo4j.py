"""Neo4j async driver wrapper for provenance graph operations.

Usage
-----
Call `get_neo4j_driver()` to obtain the singleton driver.
Use `get_neo4j_session()` as a FastAPI dependency for an async session.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from apps.api.app.config import get_settings

_driver: AsyncDriver | None = None


def get_neo4j_driver() -> AsyncDriver:
    """Return the singleton Neo4j async driver, creating it if needed."""
    global _driver
    settings = get_settings()
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
    return _driver


async def close_neo4j_driver() -> None:
    """Close the driver connection pool (call on app shutdown)."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed Neo4j async session."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        yield session


async def write_provenance_edge(
    memory_id: str,
    source_type: str,
    actor: str,
    session: AsyncSession,
) -> None:
    """Create a provenance relationship in the graph store."""
    query = """
    MERGE (s:Source {type: $source_type, actor: $actor})
    CREATE (m:Memory {memory_id: $memory_id})
    CREATE (s)-[:PROVIDED]->(m)
    """
    await session.run(query, memory_id=memory_id, source_type=source_type, actor=actor)

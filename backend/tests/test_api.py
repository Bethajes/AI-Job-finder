from httpx import AsyncClient

from app.core.config import settings


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_docs_available(client: AsyncClient) -> None:
    response = await client.get("/docs")
    assert response.status_code == 200


async def test_openapi_schema(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_PREFIX}/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/api/v1/health" in schema["paths"]
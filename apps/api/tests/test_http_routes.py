import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Category, Customer, Expense, Product, Purchase, Sale, User  # noqa: F401

REGISTER_PAYLOAD = {"email": "shop@example.com", "password": "secret123", "name": "Shop Owner"}


@pytest.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


async def _register(client: AsyncClient) -> None:
    res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 201


async def _login_token(client: AsyncClient) -> str:
    res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


async def test_register_login_me_flow(client):
    await _register(client)
    token = await _login_token(client)

    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["name"] == REGISTER_PAYLOAD["name"]
    assert body["is_active"] is True


async def test_register_rejects_duplicate_email(client):
    await _register(client)
    res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 409


async def test_login_rejects_wrong_password(client):
    await _register(client)
    res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpass"},
    )
    assert res.status_code == 401


async def test_protected_routes_require_auth(client):
    res = await client.get("/products")
    assert res.status_code in (401, 403)
    res = await client.get("/sales")
    assert res.status_code in (401, 403)
    res = await client.get("/stats/overview")
    assert res.status_code in (401, 403)


async def test_invalid_token_rejected(client):
    res = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert res.status_code == 401


async def test_update_profile(client):
    await _register(client)
    token = await _login_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.patch(
        "/auth/me", json={"store_name": "My Corner Store", "currency": "USD"}, headers=headers
    )
    assert res.status_code == 200
    body = res.json()
    assert body["store_name"] == "My Corner Store"
    assert body["currency"] == "USD"

    res = await client.get("/auth/me", headers=headers)
    assert res.json()["store_name"] == "My Corner Store"


async def test_change_password(client):
    await _register(client)
    token = await _login_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/auth/change-password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
        headers=headers,
    )
    assert res.status_code == 204

    res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "newsecret456"},
    )
    assert res.status_code == 200

    res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "secret123"},
    )
    assert res.status_code == 401


async def test_change_password_rejects_wrong_current(client):
    await _register(client)
    token = await _login_token(client)
    res = await client.post(
        "/auth/change-password",
        json={"current_password": "wrong", "new_password": "newsecret456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400


async def test_product_crud_over_http(client):
    await _register(client)
    token = await _login_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/products",
        json={
            "name": "Rice",
            "sku": "RICE-1",
            "category": "Groceries",
            "unit": "Pack",
            "purchase_price": 1000,
            "selling_price": 1200,
            "stock_quantity": 50,
            "minimum_stock": 10,
        },
        headers=headers,
    )
    assert res.status_code == 201
    product_id = res.json()["id"]

    res = await client.get(f"/products/{product_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Rice"

    res = await client.get("/products", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Rice"

    res = await client.put(
        f"/products/{product_id}",
        json={"selling_price": 1300},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["selling_price"] == "1300.00"

    res = await client.delete(f"/products/{product_id}", headers=headers)
    assert res.status_code == 204

    res = await client.get(f"/products/{product_id}", headers=headers)
    assert res.status_code == 404


async def test_users_are_isolated_over_http(client):
    await client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "secret123", "name": "User A"},
    )
    await client.post(
        "/auth/register",
        json={"email": "b@example.com", "password": "secret123", "name": "User B"},
    )

    token_a = (
        await client.post(
            "/auth/login", json={"email": "a@example.com", "password": "secret123"}
        )
    ).json()["access_token"]
    token_b = (
        await client.post(
            "/auth/login", json={"email": "b@example.com", "password": "secret123"}
        )
    ).json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    await client.post(
        "/products",
        json={
            "name": "A product",
            "sku": "A-1",
            "category": "X",
            "unit": "Piece",
            "purchase_price": 10,
            "selling_price": 15,
            "stock_quantity": 5,
            "minimum_stock": 1,
        },
        headers=headers_a,
    )

    res_b = await client.get("/products", headers=headers_b)
    assert res_b.status_code == 200
    assert res_b.json()["total"] == 0

    res_a = await client.get("/products", headers=headers_a)
    assert res_a.json()["total"] == 1


async def test_delete_account(client):
    await _register(client)
    token = await _login_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.delete("/auth/me", headers=headers)
    assert res.status_code == 204

    res = await client.get("/auth/me", headers=headers)
    assert res.status_code == 401


async def test_pagination_params(client):
    await _register(client)
    token = await _login_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(5):
        await client.post(
            "/products",
            json={
                "name": f"Product {i}",
                "sku": f"SKU-{i}",
                "category": "X",
                "unit": "Piece",
                "purchase_price": 10,
                "selling_price": 15,
                "stock_quantity": 5,
                "minimum_stock": 1,
            },
            headers=headers,
        )

    res = await client.get("/products?limit=2&offset=0", headers=headers)
    body = res.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0

    res = await client.get("/products?limit=2&offset=4", headers=headers)
    body = res.json()
    assert len(body["items"]) == 1

    res = await client.get("/products?limit=0", headers=headers)
    assert res.status_code == 422
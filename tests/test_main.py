"""Main Moduleのテストコード."""

from fastapi.testclient import TestClient

from wasanbon_webframework.main import app

client = TestClient(app)


def test_hello_world() -> None:
    """Hello World APIのテスト."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World. I am Wasanbon Webframework."}

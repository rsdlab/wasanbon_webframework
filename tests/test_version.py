"""version Moduleのテストコード."""
from typing import Generator, List, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.services import version_service


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """テストクライアントを発行する.

    Yields:
        TestClient: テストクライアント
    """
    from wasanbon_webframework.main import app

    with TestClient(app) as test_client:
        yield test_client


# GET /version
# 正常系テスト
def test_wasanbon_version(client: TestClient) -> None:
    """Wasanbon versionのテスト."""
    response = client.get("/version")
    assert response.status_code == 200
    response_dict = response.json()
    assert "wasanbon version" in response_dict
    assert "wasanbon-webframework version" in response_dict
    assert type(response_dict.get("wasanbon version").get("platform version")) is str
    assert type(response_dict.get("wasanbon version").get("wasanbon version")) is str
    assert type(response_dict.get("wasanbon-webframework version")) is str


# 異常系テスト
# response.status_codeに500を指定
def test_wasanbon_version_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon versionのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(version_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/version")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

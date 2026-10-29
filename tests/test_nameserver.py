"""nameserver Moduleのテストコード."""
from typing import Generator, List, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.services import nameserver_service


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """テストクライアントを発行する.

    Yields:
        TestClient: テストクライアント
    """
    from wasanbon_webframework.main import app

    with TestClient(app) as test_client:
        yield test_client


# POST /nameserver/start
# 正常系テスト
def test_start_name_server(client: TestClient) -> None:
    """Wasanbon nameserver startのテスト."""
    # 前処理 nameserverをstopする
    response = client.post("/nameserver/stop")

    # テスト実行
    response = client.post("/nameserver/start?port=2801")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 nameserverをstopする
    response = client.post("/nameserver/stop")
    assert response.status_code == 200


# 正常系テスト
def test_start_name_server_empty_port(client: TestClient) -> None:
    """Wasanbon nameserver startのテスト."""
    # 前処理 nameserverをstopする
    response = client.post("/nameserver/stop")

    # テスト実行
    response = client.post("/nameserver/start?port=")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 nameserverをstopする
    response = client.post("/nameserver/stop")
    assert response.status_code == 200


# 異常系テスト
def test_start_name_server_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver startのテスト."""
    # モックでコマンド実行時に失敗させる
    def mock_function_background(cmd: List[str], flg: bool) -> int:
        return 500

    monkeypatch.setattr(nameserver_service, "start_background_process_return_string", mock_function_background)

    def mock_function(cmd: str, password: str) -> Tuple[int, str, str]:
        return (500, "", "test fail")

    monkeypatch.setattr(nameserver_service, "_process_command_with_password", mock_function)

    def mock_function2(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", "test fail")

    monkeypatch.setattr(nameserver_service, "start_process_return_string", mock_function2)

    # テスト実行
    response = client.post("/nameserver/start?port=2801")
    assert response.status_code == 500


# 異常系テスト
def test_start_name_server_server_empty_port_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver startのテスト."""
    # モックでコマンド実行時に失敗させる
    def mock_function_background(cmd: List[str], flg: bool) -> int:
        return 500

    monkeypatch.setattr(nameserver_service, "start_background_process_return_string", mock_function_background)

    def mock_function(cmd: str, password: str) -> Tuple[int, str, str]:
        return (500, "", "test fail")

    monkeypatch.setattr(nameserver_service, "_process_command_with_password", mock_function)

    def mock_function2(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", "test fail")

    monkeypatch.setattr(nameserver_service, "start_process_return_string", mock_function2)

    # テスト実行
    response = client.post("/nameserver/start?port=")
    assert response.status_code == 500


# POST /nameserver/restart
# 正常系テスト
def test_restart_name_server(client: TestClient) -> None:
    """Wasanbon nameserver restartのテスト."""
    # テスト実行
    response = client.post("/nameserver/restart")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 nameserverをstopする
    response = client.post("/nameserver/stop")
    assert response.status_code == 200


# 異常系テスト
def test_restart_name_server_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver restartのテスト."""
    stdout = ""
    stderr = "test fail"

    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str], flg: bool) -> int:
        return 500

    monkeypatch.setattr(nameserver_service, "start_background_process_return_string", mock_function)

    def mock_function2(cmd: str, password: str) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(nameserver_service, "_process_command_with_password", mock_function2)

    # テスト実行
    response = client.post("/nameserver/restart")
    assert response.status_code == 500


# POST /nameserver/stop
# 正常系テスト
def test_stop_name_server(client: TestClient) -> None:
    """Wasanbon nameserver stopのテスト."""
    # 前処理 nameserverを起動する
    response = client.post("/nameserver/restart")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/nameserver/stop")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str


# 異常系テスト
def test_stop_name_server_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver stopのテスト."""
    # 前処理 nameserverを起動する
    response = client.post("/nameserver/restart")
    assert response.status_code == 200

    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(nameserver_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/nameserver/stop")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /nameserver
# 正常系テスト
def test_nameserver_check_running_running(client: TestClient) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # 前処理
    # nameserverをstartする
    response = client.post("/nameserver/start?port=2801")
    assert response.status_code == 200

    # テスト実行
    response = client.get("/nameserver/?port=2801")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # nameserverをstopする
    response = client.post("/nameserver/stop")
    assert response.status_code == 200


# 正常系テスト
def test_nameserver_check_running_not_running(client: TestClient) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # テスト実行
    response = client.get("/nameserver/?port=2801")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str


# 正常系テスト
def test_nameserver_check_running_running_empty_port(client: TestClient) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # 前処理
    # nameserverをstartする
    response = client.post("/nameserver/start?port=")
    assert response.status_code == 200

    # テスト実行
    response = client.get("/nameserver/?port=")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # nameserverをstopする
    response = client.post("/nameserver/stop")
    assert response.status_code == 200


# 正常系テスト
def test_nameserver_check_running_not_running_empty_port(client: TestClient) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # テスト実行
    response = client.get("/nameserver/?port=")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str


# 異常系テスト
def test_nameserver_check_running_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(nameserver_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/nameserver/?port=2801")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# 異常系テスト
def test_nameserver_check_running_server_empty_port_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon nameserver check_runningのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(nameserver_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/nameserver/?port=")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

"""log Moduleのテストコード."""
import os
import shutil
import zipfile
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.services.process_util import start_process_return_string


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """テストクライアントを発行する.

    Yields:
        TestClient: テストクライアント
    """
    from wasanbon_webframework.main import app

    with TestClient(app) as test_client:
        yield test_client


# GET /{ws}/packages/{name}/rtcs/logs
# 正常系テスト
def test_logs_by_rtc_dev(client: TestClient) -> None:
    """Zip of log filesのテスト."""
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 200

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_logs_by_rtc_exec(client: TestClient) -> None:
    """Zip of log filesのテスト."""
    ws = "exec"
    name = "test_project01"

    # 前処理
    # ディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 200

    # 後処理 packageを削除する
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0


# 異常系テスト
def test_logs_by_rtc_logfile_not_exist(client: TestClient) -> None:
    """Zip of log filesのテスト."""
    # logファイルがない場合、エラーになる
    ws = "dev"
    name = "test_project01"
    stderr = "LogFile not found"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # package/logを削除し、package/logを作成する
    shutil.rmtree(f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/log")
    os.mkdir(f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/log")

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 500
    assert response.json() == {"detail": stderr}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_logs_by_rtc_param_error01(client: TestClient) -> None:
    """Zip of log filesのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_logs_by_rtc_param_error02(client: TestClient) -> None:
    """Zip of log filesのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_logs_by_rtc_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Zip of log filesのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # zipfile.ZipFileにモックをあててエラーにする
    zip_mock = MagicMock()
    zip_mock.side_effect = Exception("test")
    monkeypatch.setattr(zipfile, "ZipFile", zip_mock)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    os.chdir(home_dir)
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_logs_by_rtc_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Zip of log filesのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"

    # 前処理
    # ディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # zipfile.ZipFileにモックをあててエラーにする
    zip_mock = MagicMock()
    zip_mock.side_effect = Exception("test")
    monkeypatch.setattr(zipfile, "ZipFile", zip_mock)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rts/logs")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    os.chdir(home_dir)
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0

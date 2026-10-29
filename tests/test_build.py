"""log Moduleのテストコード."""
import os
import sys
from typing import Generator, List, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.config.config import EXECUTE_WORKSPACE_BASE_PATH
from wasanbon_webframework.services import build_service
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


# POST /{ws}/packages/{name}/build
# 正常系テスト
def test_build_all_rtcs_dev(client: TestClient) -> None:
    """Rtc build allのテスト."""
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_build_all_rtcs_exec(client: TestClient) -> None:
    """Rtc build allのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# 異常系テスト
def test_build_all_rtcs_param_error01(client: TestClient) -> None:
    """Rtc build allのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_build_all_rtcs_param_error02(client: TestClient) -> None:
    """Rtc build allのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_build_all_rtcs_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Rtc build allのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_build_all_rtcs_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Rtc build allのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/build
# 正常系テスト
def test_build_rtc_dev(client: TestClient) -> None:
    """Rtc build allのテスト."""
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_build_rtc_exec(client: TestClient) -> None:
    """Rtc build allのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# 異常系テスト
def test_build_rtc_param_error01(client: TestClient) -> None:
    """Rtc build allのテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_build_rtc_param_error02(client: TestClient) -> None:
    """Rtc build allのテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name_ng"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_build_rtc_param_error03(client: TestClient) -> None:
    """Rtc build allのテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_build_rtc_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Rtc build allのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_build_rtc_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Rtc build allのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/build")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# POST /{ws}/packages/{name}/clean
# 正常系テスト
def test_clean_all_rtcs_dev(client: TestClient) -> None:
    """Clean RTCのテスト."""
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/clean")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_clean_all_rtcs_exec(client: TestClient) -> None:
    """Clean RTCのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/clean")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# 異常系テスト
def test_clean_all_rtcs_param_error01(client: TestClient) -> None:
    """Clean RTCのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/clean")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_clean_all_rtcs_param_error02(client: TestClient) -> None:
    """Clean RTCのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.post("/" + ws + "/packages/" + name + "/clean")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_clean_all_rtcs_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Clean RTCのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/clean")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_clean_all_rtcs_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Clean RTCのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/build")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/clean
# 正常系テスト
def test_clean_rtc_dev(client: TestClient) -> None:
    """Clean RTCのテスト."""
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_clean_rtc_exec(client: TestClient) -> None:
    """Clean RTCのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0


# 異常系テスト
def test_clean_rtc_param_error01(client: TestClient) -> None:
    """Clean RTCのテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_clean_rtc_param_error02(client: TestClient) -> None:
    """Clean RTCのテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name_ng"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_clean_rtc_param_error03(client: TestClient) -> None:
    """Clean RTCのテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_clean_rtc_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Clean RTCのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_clean_rtc_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Clean RTCのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # execディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageに移動する
    rtc_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(build_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/clean")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert code == 0

"""packages Moduleのテストコード."""
import os
import shutil
import stat
import sys
from typing import Any, Generator, List, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.main import app
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services import packages_service
from wasanbon_webframework.services.process_util import start_process_return_string

exec = WS.exec
dev = WS.dev
exec_package = "my_package_exec"
dev_package = "my_package_dev"
exec_rtc = "AriaRTC"
dev_rtc = "WebCamera"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """テストクライアントを発行する.

    Yields:
        TestClient: テストクライアント
    """
    # client = TestClient(app)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def setup_package_dev() -> Generator[None, None, None]:
    """Wasanbon workspaceのセットアップ."""
    # セットアップでの実行エラーは許容する
    packages_service.create_packages(dev, dev_package)
    packages_service.git_clone_rtc_service(dev, dev_package, dev_rtc)

    yield
    packages_service.delete_packages(dev_package)


@pytest.fixture
def setup_package_exec() -> Generator[None, None, None]:
    """Wasanbon workspaceのセットアップ."""
    # セットアップでの実行エラーは許容する
    packages_service.create_packages(exec, exec_package)
    packages_service.git_clone_rtc_service(exec, exec_package, exec_rtc)

    yield
    packages_service.delete_packages(exec_package)


@pytest.fixture
def setup_test_project01_dev() -> Generator[None, None, None]:
    """DWにtest_project01をセットアップ、テスト後削除する."""
    # セットアップでの実行エラーは許容する
    package_name = "test_project01"
    packages_service.git_clone_service(dev, package_name)

    yield
    packages_service.delete_packages(package_name)


@pytest.fixture
def setup_test_project01_rtc_dev() -> Generator[None, None, None]:
    """DWにtest_project01, TestIn_pyをセットアップ、テスト後削除する."""
    # セットアップでの実行エラーは許容する
    package_name = "test_project01"
    rtc_name = "TestIn_py"
    packages_service.git_clone_service(dev, package_name)
    packages_service.git_clone_rtc_service(dev, package_name, rtc_name)

    yield
    packages_service.delete_packages(package_name)


@pytest.fixture
def setup_test_package_dev() -> Generator[None, None, None]:
    """DWにtest_package, TestIn_pyをセットアップ、テスト後削除する."""
    # セットアップでの実行エラーは許容する
    package_name = "test_package"
    packages_service.create_packages(dev, package_name)

    yield
    packages_service.delete_packages(package_name)


@pytest.fixture
def setup_test_package_rtc_dev() -> Generator[None, None, None]:
    """DWにtest_package, TestIn_pyをセットアップ、テスト後削除する."""
    # セットアップでの実行エラーは許容する
    package_name = "test_package"
    rtc_name = "TestIn_py"
    packages_service.create_packages(dev, package_name)
    packages_service.git_clone_rtc_service(dev, package_name, rtc_name)

    yield
    packages_service.delete_packages(package_name)


# GET /{ws}/packages
def test_get_ws_packages_exec(client: TestClient, setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon workspaceのテスト."""
    response = client.get(f"/{exec}/packages")
    json_data = response.json()
    base_path = EXECUTE_WORKSPACE_BASE_PATH

    assert response.status_code == 200
    assert "packages" in json_data
    for item in json_data["packages"]:
        key = list(item.keys())[0]
        package_path = os.path.normpath(item[key]["path"]["root"])
        assert base_path in package_path


def test_get_ws_packages_dev(client: TestClient, setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon workspaceのテスト."""
    response = client.get(f"/{dev}/packages")
    json_data = response.json()
    base_path = DEVELOP_WORKSPACE_BASE_PATH

    assert response.status_code == 200
    assert "packages" in json_data
    for item in json_data["packages"]:
        key = list(item.keys())[0]
        package_path = os.path.normpath(item[key]["path"]["root"])
        assert base_path in package_path


def test_get_ws_packages_param_error(client: TestClient) -> None:
    # 異常系 パラメタエラー
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    response = client.get(f"/{ws}/packages")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_get_ws_packages_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 サーバーエラー
    """Wasanbon workspaceのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = None
    stderr = "Package List Get Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get(f"/{exec}/packages")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# GET /{ws}/packages/{name}/rtcs
def test_ws_packages_name_rtcs_exec(client: TestClient, setup_package_exec: Any) -> None:
    # 正常系(exec)"
    """Wasanbon workspaceのテスト."""
    response = client.get(f"/{exec}/packages/{exec_package}/rtcs")
    assert response.status_code == 200
    json_data = response.json()
    assert "rtcs" in json_data
    assert type(json_data["rtcs"]) is list


def test_ws_packages_name_rtcs_dev(client: TestClient, setup_package_dev: Any) -> None:
    # 正常系(dev)"
    """Wasanbon workspaceのテスト."""
    response = client.get(f"/{dev}/packages/{dev_package}/rtcs")
    assert response.status_code == 200
    json_data = response.json()
    assert "rtcs" in json_data
    assert type(json_data["rtcs"]) is list


def test_ws_packages_name_rtcs_param_error1(client: TestClient) -> None:
    # 異常系 パラメタエラー1　ws:NG name:OK
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    response = client.get(f"/{ws}/packages/{dev_package}/rtcs")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_ws_packages_name_rtcs_param_error2(client: TestClient) -> None:
    # 異常系 パラメタエラー2　ws:OK name:NG
    """Wasanbon workspaceのテスト."""
    pkg_name = "name-ng"

    # テスト実行
    response = client.get(f"/{dev}/packages/{pkg_name}/rtcs")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_ws_packages_name_rtcs_param_error3(client: TestClient) -> None:
    # 異常系 パラメタエラー3　ws:NG name:NG
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    pkg_name = "name-ng"
    response = client.get(f"/{ws}/packages/{pkg_name}/rtcs")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_ws_packages_name_rtcs_server_error(
    client: TestClient, setup_package_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    # 異常系 サーバーエラー
    """Wasanbon workspaceのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = "RTC List Get Out"
    stderr = "RTC List Get Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get(f"/{dev}/packages/{dev_package}/rtcs")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_ws_packages_name_rtcs_list_zero(client: TestClient, setup_test_package_dev: Any) -> None:
    # 異常系 RTCがcloneされていない状態
    """Wasanbon workspaceのテスト."""
    pkg_name = "test_package"
    response = client.get(f"/{dev}/packages/{pkg_name}/rtcs")
    assert response.status_code == 200
    json_data = response.json()
    assert "rtcs" in json_data
    assert type(json_data["rtcs"]) is list
    assert len(json_data["rtcs"]) == 0


# POST /{ws}/packages
def test_post_ws_packages_dev(client: TestClient) -> None:
    # 正常系(dev)
    """Wasanbon workspaceのテスト."""
    response = client.post(
        f"/{dev}/packages",
        json={"name": dev_package},
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert type("message" in response.json() is list)


def test_post_ws_packages_exec_bad_request(client: TestClient) -> None:
    # 異常系(exec) 書き込み禁止のWSを指定
    """Wasanbon workspaceのテスト."""
    response = client.post(
        f"/{exec}/packages",
        json={"name": exec_package},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Execute workspace is forbidden to write directly"}


def test_post_ws_packages_param_error1(client: TestClient) -> None:
    # 異常系 パラメタエラー1　ws:NG name:OK
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages",
        json={"name": dev_package},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_param_error2(client: TestClient) -> None:
    # 異常系 パラメタエラー2　ws:OK name:NG(nameでないパラメータ)
    """Wasanbon workspaceのテスト."""
    response = client.post(
        f"/{dev}/packages",
        json={"name_ng": ""},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_param_error3(client: TestClient) -> None:
    # 異常系 パラメタエラー3　ws:OK name:NG(None)
    """Wasanbon workspaceのテスト."""
    response = client.post(
        f"/{exec}/packages",
        json={"name": None},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_exist(client: TestClient, setup_package_dev: Any) -> None:
    # 異常系 すでに指定したパッケージが存在している場合
    """Wasanbon workspaceのテスト."""
    # 同じパッケージ名を指定して実行する
    # すでに作成済みのため、本テストでの作成は行わない
    response = client.post(
        f"/{dev}/packages",
        json={"name": dev_package},
    )
    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 サーバーエラー
    """Wasanbon workspaceのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "Package Create Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages",
        json={"name": dev_package},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# DELETE /{ws}/packages/{name}
def test_delete_ws_packages_name_dev(client: TestClient, setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{dev}/packages/{dev_package}")
    assert response.status_code == 200
    assert "message" in response.json()
    assert type("message" in response.json() is str)
    assert response.json() == {"message": f"Removing package {dev_package}"}


def test_delete_ws_packages_name_exec_bad_request(client: TestClient) -> None:
    # 異常系(exec) 書き込み禁止のWSを指定
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{exec}/packages/{exec_package}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Execute workspace is forbidden to write directly"}


def test_delete_ws_packages_name_param_error1(client: TestClient) -> None:
    # 異常系 パラメタエラー1　ws:NG name:OK
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    response = client.delete(f"/{ws}/packages/{dev_package}")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_delete_ws_packages_name_param_error2(client: TestClient) -> None:
    # 異常系 パラメタエラー2　ws:OK name:NG(存在しないパッケージ)
    """Wasanbon workspaceのテスト."""
    pkg_name = "package-ng"
    response = client.delete(f"/{dev}/packages/{pkg_name}")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_delete_ws_packages_not_exist(client: TestClient, setup_package_dev: Any) -> None:
    # 異常系 すでに指定したパッケージが削除されている場合
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{dev}/packages/{dev_package}")
    assert response.status_code == 200

    # 同じパッケージ名を指定して実行する
    response = client.delete(f"/{dev}/packages/{dev_package}")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_delete_ws_packages_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 サーバーエラー
    """Wasanbon workspaceのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "Package Delete Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    response = client.delete(f"/{dev}/packages/{dev_package}")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# DELETE /{ws}/packages/{name}/rtcs/{rtc_name}
def test_delete_ws_packages_name_rtcs_rtc_name_dev(client: TestClient, setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{dev_rtc}")
    assert response.status_code == 200
    assert "message" in response.json()
    assert type("message" in response.json() is str)
    assert response.json() == {"message": f"Deleting RTC ({dev_rtc}) from Package ({dev_package})"}


def test_delete_ws_packages_name_rtcs_rtc_name_exec_bad_request(client: TestClient) -> None:
    # 異常系(exec) 書き込み禁止のWSを指定
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{exec}/packages/{exec_package}/rtcs/{exec_rtc}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Execute workspace is forbidden to write directly"}


def test_delete_ws_packages_name_rtcs_rtc_name_param_error1(client: TestClient) -> None:
    # 異常系 パラメタエラー1 ws:NG name:OK rtc_name:OK
    """Wasanbon workspaceのテスト."""
    ws = "ws-ng"
    response = client.delete(f"/{ws}/packages/{dev_package}/rtcs/{dev_rtc}")
    assert response.status_code == 422
    assert "detail" in response.json()


def test_delete_ws_packages_name_rtcs_rtc_name_param_error2(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 パラメタエラー2 ws:OK name:NG rtc_name:OK
    """Wasanbon workspaceのテスト."""
    pkg_name = "name-ng"

    # テスト実行
    response = client.delete(f"/{dev}/packages/{pkg_name}/rtcs/{dev_rtc}")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_delete_ws_packages_name_rtcs_rtc_name_param_error3(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 パラメタエラー3 ws:OK name:OK rtc_name:NG
    """Wasanbon workspaceのテスト."""
    rtc_name = "BadRtc"

    # テスト実行
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{rtc_name}")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_delete_ws_packages_name_rtcs_rtc_name_param_error4(client: TestClient) -> None:
    # 異常系 パラメタエラー4 ws:OK name:NG(空文字) rtc_name:OK
    # パスパラメータが空白の場合、API不正となる
    """Wasanbon workspaceのテスト."""
    pkg_name = ""
    response = client.delete(f"/{dev}/packages/{pkg_name}/rtcs/{dev_rtc}")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json() == {"detail": "Not Found"}


def test_delete_ws_packages_name_rtcs_rtc_name_param_error5(client: TestClient) -> None:
    # 異常系 パラメタエラー5 ws:OK name:OK rtc_name:NG(空文字)
    # パスパラメータが空白の場合、API不正となる
    """Wasanbon workspaceのテスト."""
    rtc_name = ""
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{rtc_name}")
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_delete_ws_packages_name_rtcs_rtc_name_not_exist(client: TestClient, setup_package_dev: Any) -> None:
    # 異常系 すでにRTCが削除されいる場合
    """Wasanbon workspaceのテスト."""
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{dev_rtc}")
    assert response.status_code == 200

    # 同じコマンドを再度実行する
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{dev_rtc}")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_delete_ws_packages_name_rtcs_rtc_name_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    # 異常系 サーバーエラー
    """Wasanbon workspaceのテスト."""
    # モックでコマンド実行時に失敗させる
    stderr = f"Execute Failured Delete RTC ({dev_rtc}) from Package ({dev_package})"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.delete(f"/{dev}/packages/{dev_package}/rtcs/{dev_rtc}")
    assert response.status_code == 500
    assert response.json() == {"detail": stderr}


# POST /{ws}/packages/{name}/git/clone
# 正常系テスト
def test_clone_package_dev(client: TestClient) -> None:
    """Git cloneのテスト."""
    ws = "dev"
    name = "test_project01"

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_clone_package_exec(client: TestClient) -> None:
    """Git cloneのテスト."""
    ws = "exec"
    name = "test_project01"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_clone_package_exist_error(client: TestClient) -> None:
    """Git cloneのテスト."""
    # 既に存在するpackageの場合、エラーとなる
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_clone_package_param_error01(client: TestClient) -> None:
    """Git cloneのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws-ng"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_clone_package_param_error02(client: TestClient) -> None:
    """Git cloneのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name-ng"
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_clone_package_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Git cloneのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/git/clone
# 正常系テスト
def test_clone_rtc_in_package_dev(client: TestClient) -> None:
    """Git cloneのテスト."""
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_clone_rtc_in_package_exec(client: TestClient) -> None:
    """Git cloneのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_clone_rtc_in_package_param_error01(client: TestClient) -> None:
    """Git cloneのテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws-ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_clone_rtc_in_package_param_error02(client: TestClient) -> None:
    """Git cloneのテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name-ng"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_clone_rtc_in_package_param_error03(client: TestClient) -> None:
    """Git cloneのテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_clone_rtc_in_package_server_error(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Git cloneのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/git/init
# 正常系テスト
def test_git_init_package_dev(client: TestClient) -> None:
    """Git initのテスト."""
    ws = "dev"
    name = "test_package"

    # 前処理
    # packageを作成する
    response = client.post(
        "/" + ws + "/packages",
        json={"name": name},
    )

    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/init")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_init_package_exec(client: TestClient) -> None:
    """Git initのテスト."""
    ws = "exec"
    name = "test_package"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/git/init")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_init_package_param_error01(client: TestClient) -> None:
    """Git initのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws-ng"
    name = "test_package"
    response = client.post("/" + ws + "/packages/" + name + "/git/init")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_init_package_param_error02(client: TestClient) -> None:
    """Git initのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name-ng"
    response = client.post("/" + ws + "/packages/" + name + "/git/init")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_init_package_server_error(
    client: TestClient, setup_test_package_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Git initのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_package"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/init")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/git/init
# 正常系テスト
def test_git_init_rtc_package_dev(client: TestClient) -> None:
    """Git initのテスト."""
    ws = "dev"
    name = "test_package"
    rtc_name = "TestIn_py"

    # 前処理
    # packageを作成する
    response = client.post(
        "/" + ws + "/packages",
        json={"name": name},
    )
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # /{name}/rtc/{rtc_name}/.gitを削除する
    rtc_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}/.git"

    for root, dirs, files in os.walk(rtc_path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree(rtc_path)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_init_rtc_package_exec(client: TestClient) -> None:
    """Git initのテスト."""
    ws = "exec"
    name = "test_package"
    rtc_name = "TestIn_py"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_init_rtc_package_param_error01(client: TestClient) -> None:
    """Git initのテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws-ng"
    name = "test_package"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_init_rtc_package_param_error02(client: TestClient) -> None:
    """Git initのテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name-ng"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_init_rtc_package_param_error03(client: TestClient) -> None:
    """Git initのテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_package"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageを作成する
    response = client.post(
        "/" + ws + "/packages",
        json={"name": name},
    )
    assert response.status_code == 200

    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_init_rtc_package_server_error(
    client: TestClient, setup_test_package_rtc_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Git initのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_package"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理 /{name}/rtc/{rtc_name}/.gitを削除する
    rtc_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}/.git"

    for root, dirs, files in os.walk(rtc_path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree(rtc_path)

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/init")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/sync_rtc
# 正常系テスト
def test_sync_rtcs_in_package_dev(client: TestClient) -> None:
    """Admin syncのテスト."""
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/sync_rtc")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_sync_rtcs_in_package_exec(client: TestClient) -> None:
    """Admin syncのテスト."""
    ws = "exec"
    name = "test_project01"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/sync_rtc")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_sync_rtcs_in_package_param_error01(client: TestClient) -> None:
    """Admin syncのテスト."""
    # パラメタエラー1 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.post("/" + ws + "/packages/" + name + "/sync_rtc")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_sync_rtcs_in_package_param_error02(client: TestClient) -> None:
    """Admin syncのテスト."""
    # パラメタエラー2 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/sync_rtc")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_sync_rtcs_in_package_server_error(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Admin syncのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/sync_rtc")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/git/commit
# 正常系テスト
def test_git_commit_package_dev(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post(
        "/" + ws + "/packages/" + name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_commit_package_exec(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    ws = "exec"
    name = "test_project01"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post(
        "/" + ws + "/packages/" + name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_commit_package_param_error01(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.post(
        "/" + ws + "/packages/" + name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_commit_package_param_error02(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.post(
        "/" + ws + "/packages/" + name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_commit_package_param_error03(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー3 ws:OK name:NG リクエストボディのパラメラ不足
    ws = "dev"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/git/commit")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_commit_package_server_error(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Admin commit <COMMENT>のテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post(
        "/" + ws + "/packages/" + name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/git/commit
# 正常系テスト
def test_git_commit_rtc_dev(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
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
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_commit_rtc_exec(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_commit_rtc_param_error01(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_commit_rtc_param_error02(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name_ng"
    rtc_name = "TestIn_py"
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_commit_rtc_param_error03(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_commit_rtc_param_error04(client: TestClient) -> None:
    """Admin commit <COMMENT>のテスト."""
    # パラメタエラー4 ws:OK name:OK rtc_name:OK リクエストボディのパラメタ不足
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
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit")
    assert response.status_code == 422
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_commit_rtc_server_error(
    client: TestClient, setup_test_project01_rtc_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Admin commit <COMMENT>のテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/commit",
        json={"comment": "hogehoge"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/git/push
# 正常系テスト
def test_git_push_package_dev(client: TestClient) -> None:
    """Admin pushのテスト."""
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/push")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_push_package_exec(client: TestClient) -> None:
    """Admin pushのテスト."""
    ws = "exec"
    name = "test_project01"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/git/push")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_push_package_param_error01(client: TestClient) -> None:
    """Admin pushのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.post("/" + ws + "/packages/" + name + "/git/push")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_push_package_param_error02(client: TestClient) -> None:
    """Admin pushのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.post("/" + ws + "/packages/" + name + "/git/push")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_push_package_server_error(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Admin pushのテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/git/push")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# POST /{ws}/packages/{name}/rtcs/{rtc_name}/git/push
# 正常系テスト
def test_git_push_rtc_dev(client: TestClient) -> None:
    """Repository push <RTC_NAME>のテスト."""
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

    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_push_rtc_exec(client: TestClient) -> None:
    """Repository push <RTC_NAME>のテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_push_rtc_param_error01(client: TestClient) -> None:
    """Repository push <RTC_NAME>のテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_push_rtc_param_error02(client: TestClient) -> None:
    """Repository push <RTC_NAME>のテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name_ng"
    rtc_name = "TestIn_py"
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_push_rtc_param_error03(client: TestClient) -> None:
    """Repository push <RTC_NAME>のテスト."""
    # パラメタエラー3 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_push_rtc_server_error(
    client: TestClient, setup_test_project01_rtc_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Repository push <RTC_NAME>のテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.post("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/push")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# PUT  /{ws}/packages/{name}/git/remote
# 正常系テスト
def test_git_add_remote_to_package_dev(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    ws = "dev"
    name = "test_project01"
    url = "hogehoge"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    os.chdir(dir_path)

    # リモート先を削除する
    code, stdout, stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    # テスト実行
    response = client.put("/" + ws + "/packages/" + name + "/git/remote", json={"url": url})
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_add_remote_to_package_exec(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    ws = "exec"
    name = "test_project01"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.put("/" + ws + "/packages/" + name + "/git/remote", json={"url": "hogehoge"})
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_add_remote_to_package_param_error01(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー1 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.put("/" + ws + "/packages/" + name + "/git/remote", json={"url": "hogehoge"})
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_add_remote_to_package_param_error02(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー2 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.put("/" + ws + "/packages/" + name + "/git/remote", json={"url": "hogehoge"})
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_add_remote_to_package_param_error03(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー3 ws:OK name:OK リクエストボディのパラメタ不足
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    os.chdir(dir_path)

    # リモート先を削除する
    code, stdout, stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    response = client.put("/" + ws + "/packages/" + name + "/git/remote")
    assert response.status_code == 422
    assert "detail" in response.json()

    # 後処理 packageを削除する
    os.chdir(home_dir)
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_add_remote_to_package_server_error(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Git remote add origin <URL>のテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # リモート先を削除する
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    os.chdir(dir_path)
    code, stdout, stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put("/" + ws + "/packages/" + name + "/git/remote", json={"url": "hogehoge"})
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# PUT  /{ws}/packages/{name}/rtcs/{rtc_name}/git/remote
# 正常系テスト
def test_git_add_remote_to_rtc_dev(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
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

    # リモート先を削除する
    # パッケージのディレクトリに移動する
    dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}"
    os.chdir(dir_path)
    code, stdout, stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    # テスト実行
    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_add_remote_to_rtc_exec(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # 書き込み動作になるためresponse.status_codeは400になる
    stderr = "Execute workspace is forbidden to write directly"
    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": stderr}


# 異常系テスト
def test_git_add_remote_to_rtc_param_error01(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー1 ws:NG name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


# 異常系テスト
def test_git_add_remote_to_rtc_param_error02(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー2 ws:OK name:NG rtc_name:OK
    ws = "dev"
    name = "name_ng"
    rtc_name = "TestIn_py"
    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 500
    assert "detail" in response.json()


# 異常系テスト
def test_git_add_remote_to_rtc_param_error03(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー1 ws:OK name:OK rtc_name:NG
    ws = "dev"
    name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 500
    assert "detail" in response.json()

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_add_remote_to_rtc_param_error04(client: TestClient) -> None:
    """Git remote add origin <URL>のテスト."""
    # パラメタエラー1 ws:OK name:OK rtc_name:NG リクエストボディのパラメタ不足
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

    # リモート先を削除する
    # パッケージのディレクトリに移動する
    dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}"
    os.chdir(dir_path)
    code, stdout, stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    # テスト実行
    response = client.put("/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote")
    assert response.status_code == 422
    assert "detail" in response.json()

    # 後処理 packageを削除する
    os.chdir(home_dir)
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 異常系テスト
def test_git_add_remote_to_rtc_server_error(
    client: TestClient, setup_test_project01_rtc_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Git remote add origin <URL>のテスト."""
    # サーバーエラー
    ws = "dev"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # リモート先を削除する
    # パッケージのディレクトリに移動する
    dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}"
    os.chdir(dir_path)
    code, clone_stdout, clone_stderr = start_process_return_string(["git", "remote", "remove", "origin"])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put(
        "/" + ws + "/packages/" + name + "/rtcs/" + rtc_name + "/git/remote", json={"url": "hogehoge"}
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# GET /{ws}/packages/{name}/git/status
# 正常系テスト
def test_git_status_of_package_dev(client: TestClient) -> None:
    """Admin statusのテスト."""
    ws = "dev"
    name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 200
    response_dict = response.json()
    assert "status" in response_dict
    status_list = list(response_dict.get("status").values())
    for values in status_list:
        assert type(values) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_status_of_package_exec(client: TestClient) -> None:
    """Admin statusのテスト."""
    ws = "exec"
    name = "test_project01"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 200
    response_dict = response.json()
    assert "status" in response_dict
    status_list = list(response_dict.get("status").values())
    for values in status_list:
        assert type(values) is str

    # 後処理 packageを削除する
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0


# 異常系テスト
def test_git_status_of_package_param_error01(client: TestClient) -> None:
    """Admin statusのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 422


# 異常系テスト
def test_git_status_of_package_param_error02(client: TestClient) -> None:
    """Admin statusのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 500


# 異常系テスト
def test_git_status_of_package_server_error01(
    client: TestClient, setup_test_project01_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Admin statusのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# 異常系テスト
def test_git_status_of_package_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Admin statusのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/git/status")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0


# GET /{ws}/packages/{name}/rtcs/git/status
# 正常系テスト
def test_git_status_of_all_rtcs_dev(client: TestClient) -> None:
    """Repository statusのテスト."""
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
    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 200
    response_dict = response.json()
    assert "status" in response_dict
    status_list = list(response_dict.get("status").values())
    for values in status_list:
        assert type(values) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + name)
    assert response.status_code == 200


# 正常系テスト
def test_git_status_of_all_rtcs_exec(client: TestClient) -> None:
    """Repository statusのテスト."""
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageディレクトリに移動する
    dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 200
    response_dict = response.json()
    assert "status" in response_dict
    status_list = list(response_dict.get("status").values())
    for values in status_list:
        assert type(values) is str

    # 後処理 packageを削除する
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0


# 異常系テスト
def test_git_status_of_all_rtcs_param_error01(client: TestClient) -> None:
    """Repository statusのテスト."""
    # パラメタエラー1 ws:NG name:OK
    ws = "ws_ng"
    name = "test_project01"
    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 422


# 異常系テスト
def test_git_status_of_all_rtcs_param_error02(client: TestClient) -> None:
    """Repository statusのテスト."""
    # パラメタエラー2 ws:OK name:NG
    ws = "dev"
    name = "name_ng"
    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 500


# 異常系テスト
def test_git_status_of_all_rtcs_server_error01(
    client: TestClient, setup_test_project01_rtc_dev: Any, monkeypatch: MonkeyPatch
) -> None:
    """Repository statusのテスト."""
    # サーバーエラー1
    ws = "dev"
    name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# 異常系テスト
def test_git_status_of_all_rtcs_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Repository statusのテスト."""
    # サーバーエラー2
    ws = "exec"
    name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", name])
    assert code == 0

    # packageディレクトリに移動する
    dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}"
    os.chdir(dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(packages_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.get("/" + ws + "/packages/" + name + "/rtcs/git/status")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    del_code, stdout, stderr = start_process_return_string(["wasanbon-admin.py", "package", "delete", "-r", name])
    assert del_code == 0

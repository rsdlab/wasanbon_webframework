"""execution Moduleのテストコード."""
import os
from time import sleep
from typing import Any, Generator, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import wasanbon_webframework.services.common_service as common_service
from wasanbon_webframework.config.config import EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.main import app
from wasanbon_webframework.models.rtcname import RtcName
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services import execution_service as service
from wasanbon_webframework.services import packages_service as pkg_service
from wasanbon_webframework.services.process_util import (
    start_background_process_return_string,
    start_process_return_string,
)
from wasanbon_webframework.services.wasanbon_util import _generate_mgr_command, _generate_wasanbon_admin_command

client = TestClient(app)

exec = WS.exec
dev = WS.dev
exec_package = "my_package_exec"
dev_package = "my_package_dev"
exec_rtc = "AriaRTC"
dev_rtc = "WebCamera"

clone_package = "test_project01"
clone_rtc_run = "TestIn_cpp"
clone_rtc_run2 = "TestOut_cpp"


@pytest.fixture
def setup_package_dev() -> Generator[None, None, None]:
    """Wasanbon executionのセットアップ."""
    # セットアップでの実行エラーは許容する
    pkg_service.create_packages(dev, dev_package)
    pkg_service.git_clone_rtc_service(dev, dev_package, dev_rtc)
    nameserver_start()

    yield
    service.kill_process(dev_rtc)
    nameserver_stop()
    pkg_service.delete_packages(dev_package)


@pytest.fixture
def setup_package_dev_not_rtc() -> Generator[None, None, None]:
    """Wasanbon executionのセットアップ."""
    # セットアップでの実行エラーは許容する
    pkg_service.create_packages(dev, dev_package)
    nameserver_start()

    yield
    nameserver_stop()
    pkg_service.delete_packages(dev_package)


@pytest.fixture
def setup_package_exec() -> Generator[None, None, None]:
    """Wasanbon executionのセットアップ."""
    nameserver_start()
    # セットアップでの実行エラーは許容する
    pkg_service.create_packages(exec, exec_package)
    # git_clone_rtc_service_tmp(exec_package, exec_rtc)
    pkg_service.git_clone_rtc_service(exec, exec_package, exec_rtc)

    yield
    service.kill_process(exec_rtc)
    nameserver_stop()
    pkg_service.delete_packages(exec_package)


def nameserver_start() -> None:
    """Wasanbon executionのセットアップ."""
    options = [
        "nameserver",
        "start",
    ]
    command = _generate_wasanbon_admin_command(options)
    start_background_process_return_string(command, True)


def nameserver_stop() -> None:
    """Wasanbon executionのセットアップ."""
    options = [
        "nameserver",
        "stop",
    ]
    command = _generate_wasanbon_admin_command(options)
    start_process_return_string(command)


def start_rtc(ws: WS, pkg_name: str, rtc_name: Optional[str]) -> None:
    """Wasanbon executionのセットアップ."""
    # 起動／停止のテストがあるため、テストごとに呼び出す
    if rtc_name is None:
        rtc_data = None
    else:
        rtc_data = RtcName(rtc_name=rtc_name)
    service.start_system(ws, pkg_name, rtc_data)
    sleep(10)


@pytest.fixture
def setup_package_clone_dev() -> Generator[None, None, None]:
    """Wasanbon executionのセットアップ."""
    # パッケージ作成、RTC起動、コマンド発行
    pkg_service.git_clone_service(dev, clone_package)
    rtc_bilud(dev)
    # ネームサーバ起動
    nameserver_start()

    yield
    # システム停止
    service.terminate_system(dev, clone_package, None)
    service.kill_process(clone_rtc_run)
    service.kill_process(clone_rtc_run2)
    # ネームサーバ停止
    nameserver_stop()
    # パッケージ削除
    pkg_service.delete_packages(clone_package)


@pytest.fixture
def setup_package_clone_exec() -> Generator[None, None, None]:
    """Wasanbon executionのセットアップ."""
    # パッケージ作成、RTC起動、コマンド発行
    git_clone_service_tmp(clone_package)
    # pkg_service.git_clone_service(exec, clone_package)
    rtc_bilud(exec)
    # ネームサーバ起動
    nameserver_start()

    yield
    # システム停止
    service.terminate_system(exec, clone_package, None)
    service.kill_process(clone_rtc_run)
    service.kill_process(clone_rtc_run2)
    # ネームサーバ停止
    nameserver_stop()
    # パッケージ削除
    pkg_service.delete_packages(clone_package)


def git_clone_service_tmp(name: str) -> Tuple[int, str, str]:
    """Wasanbon executionのセットアップ."""
    dir_path = EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)
    options = ["repository", "clone", name, "-v"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)
    os.chdir(home_dir)
    return (code, stdout, stderr)


def rtc_bilud(ws: WS) -> None:
    """Wasanbon executionのセットアップ."""
    # ビルドしないと動かない？
    path = os.path.join(common_service.get_basepath(ws), clone_package)
    options1 = ["rtc", "build", clone_rtc_run]
    options2 = ["rtc", "build", clone_rtc_run2]
    os.chdir(path)
    command1 = _generate_mgr_command(path, options1)
    start_process_return_string(command1)
    command2 = _generate_mgr_command(path, options2)
    start_process_return_string(command2)
    os.chdir(home_dir)


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/run
def test_post_ws_packages_name_rtc_run_exec(setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon executionのテスト."""
    response = client.post(f"/{exec}/packages/{exec_package}/rts/run")

    assert response.status_code == 200
    assert response.json() == {"message": f"System Started ({exec_package})"}


def test_post_ws_packages_name_rtc_run_dev(setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    response = client.post(f"/{dev}/packages/{dev_package}/rts/run")

    assert response.status_code == 200
    assert response.json() == {"message": f"System Started ({dev_package})"}


def test_post_ws_packages_name_rtc_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(f"/{ws}/packages/{dev_package}/rts/run")

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rtc_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(f"/{dev}/packages/{name}/rts/run")

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rtc_run_not_rtc(setup_package_dev_not_rtc: Any) -> None:
    # 異常系(RTCのインストールなし)
    """Wasanbon executionのテスト."""
    response = client.post(f"/{dev}/packages/{dev_package}/rts/run")

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": "", "stderr": f"RTC not installed in Package ({dev_package})"}}


def test_post_ws_packages_name_rtc_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(コマンドエラー)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str], wait_flg: bool) -> int:
        return 1

    monkeypatch.setattr(service, "start_background_process_return_string", mock_function)

    # テスト実行
    response = client.post(f"/{dev}/packages/{dev_package}/rts/run")
    assert response.status_code == 500
    assert "detail" in response.json()


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/start
def test_post_ws_packages_name_rts_start_exec(setup_package_exec: Any) -> None:
    # 正常系(exec system-run)
    """Wasanbon executionのテスト."""
    response = client.post(
        f"/{exec}/packages/{exec_package}/rts/start",
        # json={"rtc_name": ""},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_start_exec_rtc_run(setup_package_clone_exec: Any) -> None:
    # 正常系(exec rtc-run)
    """Wasanbon executionのテスト."""
    response = client.post(
        f"/{exec}/packages/{clone_package}/rts/start",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RTC Started ({clone_rtc_run})"}


def test_post_ws_packages_name_rts_start_dev(setup_package_dev: Any) -> None:
    # 正常系(dev system-run)
    """Wasanbon executionのテスト."""
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/start",
        # json={"rtc_name": ""},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_start_dev_rtc_run(setup_package_clone_dev: Any) -> None:
    # 正常系(dev rtc-run)
    """Wasanbon executionのテスト."""
    response = client.post(
        f"/{dev}/packages/{clone_package}/rts/start",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RTC Started ({clone_rtc_run})"}


def test_post_ws_packages_name_rts_start_dev_rtc_started(setup_package_clone_dev: Any) -> None:
    # 異常系(dev rtc-run　RTC起動済み)
    """Wasanbon executionのテスト."""
    response = client.post(
        f"/{dev}/packages/{clone_package}/rts/start",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RTC Started ({clone_rtc_run})"}

    # 再度、同じRTCを起動する
    response = client.post(
        f"/{dev}/packages/{clone_package}/rts/start",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": "", "stderr": f"RTC Process Already Started ({clone_rtc_run})"}}


def test_post_ws_packages_name_rts_start_param_error() -> None:
    # 異常系(dev ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages/{dev_package}/rts/start",
        json={"rtc_name": dev_rtc},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_start_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(
        f"/{dev}/packages/{name}/rts/start",
        json={"rtc_name": dev_rtc},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_start_param_error3(setup_package_dev: Any) -> None:
    # 異常系(rtc_name:NG 存在しないRTC)
    """Wasanbon executionのテスト."""
    rtc_name = "rtc-ng"
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/start",
        json={"rtc_name": rtc_name},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": "", "stderr": f"RTC is not installed ({rtc_name})"}}


def test_post_ws_packages_name_rts_start_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー System開始)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str], wait_flg: bool) -> int:
        return 1

    monkeypatch.setattr(service, "start_background_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/start",
        # json={"rtc_name": None},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_start_server_error2(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー RTC開始)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str]) -> int:
        return 1

    monkeypatch.setattr(service, "start_background_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/start",
        json={"rtc_name": dev_rtc},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/connect
def test_post_ws_packages_name_rts_connect_exec(setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon executionのテスト."""
    start_rtc(exec, exec_package, exec_rtc)
    response = client.post(
        f"/{exec}/packages/{exec_package}/rts/connect",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"rtresurrect": "RT System Connection Resurrected"}


def test_post_ws_packages_name_rts_connect_dev(setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    start_rtc(dev, dev_package, dev_rtc)
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/connect",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"rtresurrect": "RT System Connection Resurrected"}


def test_post_ws_packages_name_rts_connect_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages/{dev_package}/rts/connect",
        json={},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_connect_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(
        f"/{dev}/packages/{name}/rts/connect",
        json={},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_connect_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー)
    """Wasanbon executionのテスト."""
    start_rtc(dev, dev_package, dev_rtc)
    # モックでコマンド実行時に失敗させる
    stdout = "RTC Connect Out"
    stderr = "RTC Connect Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/connect",
        json={},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/disconnect
def test_post_ws_packages_name_rts_disconnect_exec(setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon executionのテスト."""
    start_rtc(exec, exec_package, exec_rtc)
    response = client.post(
        f"/{exec}/packages/{exec_package}/rts/disconnect",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"rtteardown": "RT System Removed Connection"}


def test_post_ws_packages_name_rts_disconnect_dev(setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    start_rtc(dev, dev_package, dev_rtc)
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/disconnect",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"rtteardown": "RT System Removed Connection"}


def test_post_ws_packages_name_rts_disconnect_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages/{dev_package}/rts/disconnect",
        json={},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_disconnect_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(
        f"/{dev}/packages/{name}/rts/disconnect",
        json={},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_disconnect_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    start_rtc(dev, dev_package, dev_rtc)
    stdout = "RTC Disconnect Out"
    stderr = "RTC Disconnect Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/disconnect",
        json={},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/activate
def test_post_ws_packages_name_rts_activate_exec(setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon executionのテスト."""
    start_rtc(exec, exec_package, exec_rtc)
    response = client.post(
        f"/{exec}/packages/{exec_package}/rts/activate",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RT System Started ({exec_package})"}


def test_post_ws_packages_name_rts_activate_dev(setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    start_rtc(dev, dev_package, dev_rtc)
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/activate",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RT System Started ({dev_package})"}


def test_post_ws_packages_name_rts_activate_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages/{dev_package}/rts/activate",
        json={},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_activate_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(
        f"/{dev}/packages/{name}/rts/activate",
        json={},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_activate_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    start_rtc(dev, dev_package, dev_rtc)
    stdout = "RTC Activate Out"
    stderr = "RTC Activate Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/activate",
        json={},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/deactivate
def test_post_ws_packages_name_rts_deactivate_exec(setup_package_exec: Any) -> None:
    # 正常系(exec)
    """Wasanbon executionのテスト."""
    start_rtc(exec, exec_package, exec_rtc)
    response = client.post(
        f"/{exec}/packages/{exec_package}/rts/deactivate",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RT System Stoped ({exec_package})"}


def test_post_ws_packages_name_rts_deactivate_dev(setup_package_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    start_rtc(dev, dev_package, dev_rtc)
    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/deactivate",
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"RT System Stoped ({dev_package})"}


def test_post_ws_packages_name_rts_deactivate_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.post(
        f"/{ws}/packages/{dev_package}/rts/deactivate",
        json={},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_deactivate_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.post(
        f"/{dev}/packages/{name}/rts/deactivate",
        json={},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_deactivate_server_error(setup_package_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    start_rtc(dev, dev_package, dev_rtc)
    stdout = "RTC Deactivate Out"
    stderr = "RTC Deactivate Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, stdout, stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    response = client.post(
        f"/{dev}/packages/{dev_package}/rts/deactivate",
        json={},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# ----------------------------------------
# GET /{ws}/packages/{name}/rts/status
def test_get_ws_packages_name_rts_status(setup_package_clone_dev: Any) -> None:
    # 正常系(dev)
    """Wasanbon executionのテスト."""
    # システム起動
    service.start_system(dev, clone_package, None)

    response = client.get(
        f"/{dev}/packages/{clone_package}/rts/status",
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "successful_RTCs" in json_data
    assert "failure_RTCs" in json_data


def test_get_ws_packages_name_rts_status_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    response = client.get(
        f"/{ws}/packages/{clone_package}/rts/status",
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_get_ws_packages_name_rts_status_param_error2() -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    response = client.get(
        f"/{dev}/packages/{name}/rts/status",
    )

    assert response.status_code == 500
    response_dict = response.json()
    assert "detail" in response_dict
    assert type(response_dict["detail"]["stdout"]) is list
    assert type(response_dict["detail"]["stderr"]) is list


def test_get_ws_packages_name_rts_status_server_error(setup_package_clone_dev: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(サーバーエラー)
    """Wasanbon executionのテスト."""
    # モックでコマンド実行時に失敗させる
    stderr = "RTC Status Get Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    """Wasanbon executionのテスト."""
    response = client.get(
        f"/{dev}/packages/{clone_package}/rts/status",
    )

    # レスポンスでは500は返却されない
    assert response.status_code == 200
    assert response.json() == {"failure_RTCs": [], "successful_RTCs": []}


# ----------------------------------------
# POST /{ws}/packages/{name}/rts/terminate
def test_post_ws_packages_name_rts_terminate_exec(setup_package_clone_exec: Any) -> None:
    # 正常系(exec system-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(exec, clone_package, None)
    # テスト実施
    response = client.post(
        f"/{exec}/packages/{clone_package}/rts/terminate",
        # json={"rtc_name": ""},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_terminate_dev(setup_package_clone_dev: Any) -> None:
    # 正常系(dev system-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(dev, clone_package, None)
    # テスト実施
    response = client.post(
        f"/{dev}/packages/{clone_package}/rts/terminate",
        # json={"rtc_name": ""},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_terminate_exec2(setup_package_clone_exec: Any) -> None:
    # 正常系(exec rtc-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(exec, clone_package, clone_rtc_run)
    # テスト実施
    response = client.post(
        f"/{exec}/packages/{clone_package}/rts/terminate",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_terminate_dev2(setup_package_clone_dev: Any) -> None:
    # 正常系(dev rtc-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(dev, clone_package, clone_rtc_run)
    # テスト実施
    response = client.post(
        f"/{dev}/packages/{clone_package}/rts/terminate",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 200
    assert "message" in response.json()


def test_post_ws_packages_name_rts_terminate_param_error(setup_package_clone_exec: Any) -> None:
    # 異常系(ws:NG)
    """Wasanbon executionのテスト."""
    ws = "ws-ng"
    # システム起動
    start_rtc(exec, clone_package, clone_rtc_run)
    # テスト実施
    response = client.post(
        f"/{ws}/packages/{clone_package}/rts/terminate",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_terminate_param_error2(setup_package_clone_exec: Any) -> None:
    # 異常系(name:NG)
    """Wasanbon executionのテスト."""
    name = "package-ng"
    # システム起動
    start_rtc(exec, clone_package, clone_rtc_run)
    # テスト実施
    response = client.post(
        f"/{exec}/packages/{name}/rts/terminate",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_terminate_server_error(
    setup_package_clone_exec: Any, monkeypatch: MonkeyPatch
) -> None:
    # 異常系(サーバーエラー system-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(exec, clone_package, None)
    # モックでコマンド実行時に失敗させる
    stderr = "Terminate Launched System Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    # テスト実施
    response = client.post(
        f"/{exec}/packages/{clone_package}/rts/terminate",
        # json={"rtc_name": ""},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_ws_packages_name_rts_terminate_server_error2(
    setup_package_clone_exec: Any, monkeypatch: MonkeyPatch
) -> None:
    # 異常系(サーバーエラー rtc-terminate)
    """Wasanbon executionのテスト."""
    # システム起動
    start_rtc(exec, clone_package, clone_rtc_run)
    # モックでコマンド実行時に失敗させる
    stderr = "Terminate Launched System Error"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(service, "start_process_return_string", mock_function)

    # テスト実施
    response = client.post(
        f"/{exec}/packages/{clone_package}/rts/terminate",
        json={"rtc_name": clone_rtc_run},
    )

    assert response.status_code == 500
    assert "detail" in response.json()

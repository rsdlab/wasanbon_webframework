"""binder Moduleのテストコード."""
import logging
import os
import shutil
import stat
import sys
from typing import Generator, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import wasanbon_webframework.config.config as config
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services import binder_service
from wasanbon_webframework.services.process_util import start_process_return_string

logger = logging.getLogger(__name__)

home_dir = os.path.expanduser("~")
binder_dir = os.path.join(home_dir, ".wasanbon/binder")


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """テストクライアントを発行する.

    Yields:
        TestClient: テストクライアント
    """
    from wasanbon_webframework.main import app

    with TestClient(app) as test_client:
        yield test_client


def delete_binder(binder_name: str) -> None:
    """バインダーを削除する.

    Args:
        binder_name(str): バインダー名
    """
    try:
        for root, dirs, files in os.walk(f"{binder_dir}/{binder_name}_owner"):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(f"{binder_dir}/{binder_name}_owner")
        logger.error("removed create binder " + binder_name)
    except Exception as e:
        logger.error(e, exc_info=True)


# -------------------------------------------------
# GET /binders
# 正常系
def test_get_binder(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    response = client.get("/binders")
    assert response.status_code == 200
    response_dict = response.json()
    assert "binders" in response_dict
    assert type(response_dict["binders"]) is list


# 異常系 サーバーエラー
def test_get_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = None
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.get("/binders")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# -------------------------------------------------
# POST /binders/update
# 正常系
def test_update_binder(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_update_binder01"
    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    response = client.post("/binders/update")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    delete_binder(binder_name)


# 異常系 サーバーエラー
def test_update_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_update_binder02"
    stdout = ""
    stderr = "test fail"
    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.post("/binders/update")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    delete_binder(binder_name)


# -------------------------------------------------
# GET /binders/packages
# 正常系
def test_get_packages_in_binders(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    response = client.get("/binders/packages")
    assert response.status_code == 200
    response_dict = response.json()
    assert "packages" in response_dict
    assert type(response_dict["packages"]) is list


# 異常系 サーバーエラー
def test_get_packages_in_binders_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = None
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.get("/binders/packages")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# -------------------------------------------------
# GET /binders/rtcs
# 正常系
def test_get_rtcs_in_binders(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    response = client.get("/binders/rtcs")
    assert response.status_code == 200
    response_dict = response.json()
    assert "rtcs" in response_dict
    assert type(response_dict["rtcs"]) is list


# 異常系 サーバーエラー
def test_get_rtcs_in_binders_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # モックでコマンド実行時に失敗させる
    stdout = None
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.get("/binders/rtcs")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# -------------------------------------------------
# POST /binders
# 正常系
def test_create_binder(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_create_binder01"
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    # 後処理
    delete_binder(binder_name)


# 異常系 パラメタエラー (リクエストボディのパラメラ不足)
def test_create_binder_param_error1(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_create_binder02"
    response = client.post(
        "/binders",
        json={
            "username": binder_name,
        },
    )
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict


# 異常系 パラメタエラー (トークンが不正)
def test_create_binder_param_error2(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_create_binder03"
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "error_token"},
    )
    assert response.status_code == 500
    response_dict = response.json()
    assert "detail" in response_dict


# 異常系 サーバーエラー
def test_create_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_create_binder04"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


# -------------------------------------------------
# POST /binders/{name}/commit
# 正常系
def test_commit_binder(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_commit_binder01"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + binder_name + "_owner/commit", json={"comment": "commit message"})
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict

    # 後処理
    delete_binder(binder_name)


# 異常系 パラメタエラー (binder名不正)
def test_commit_binder_param_error1(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_commit_binder02"
    error_name = "ng_name"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + error_name + "/commit", json={"comment": "commit message"})
    assert response.status_code == 500
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    delete_binder(binder_name)


# 異常系 パラメタエラー (リクエストボディのパラメラ不足)
def test_commit_binder_param_error2(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_commit_binder03"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + binder_name + "/commit", json={})
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    delete_binder(binder_name)


# 異常系 サーバーエラー
def test_commit_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_commit_binder04"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.post("/binders/" + binder_name + "/commit", json={"comment": "commit message"})
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理
    delete_binder(binder_name)


# -------------------------------------------------
# POST /binders/{name}/push
# 正常系
def test_push_binder(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_push_binder01"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + binder_name + "_owner/push", json={"comment": "commit message"})
    assert response.status_code == 500
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    delete_binder(binder_name)


# 異常系 パラメタエラー (binder名不正)
def test_push_binder_param_error1(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_push_binder02"
    error_name = "ng_name"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + error_name + "/push", json={"comment": "commit message"})
    assert response.status_code == 500
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    delete_binder(binder_name)


# 異常系 パラメタエラー (リクエストボディのパラメラ不足)
def test_push_binder_param_error2(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    binder_name = "test_push_binder03"
    # 前処理
    # バインダー作成
    response = client.post(
        "/binders", json={"username": binder_name, "token": "YOUR_TOKEN"}
    )

    # メイン処理
    response = client.post("/binders/" + binder_name + "/push", json={})
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    delete_binder(binder_name)


# -------------------------------------------------
# POST /binders/{name}/packages
# 正常系(dev)
def test_add_package_to_binder_dev(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_package_package01"
    binder_name = "test_add_package_binder01"
    # 前処理
    # パッケージ作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post("/binders/" + binder_name + "_owner/packages", json={"ws": ws, "package_name": package_name})
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{ws}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 正常系(exec)
def test_add_package_to_binder_exec(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "exec"
    package_name = "test_project01"
    binder_name = "test_add_package_binder02"
    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", package_name])
    assert code == 0

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post("/binders/" + binder_name + "_owner/packages", json={"ws": ws, "package_name": package_name})
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    # 後処理
    # パッケージ削除
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )

    # バインダー削除
    delete_binder(binder_name)


# 異常系 パラメタエラー (リクエストボディのパラメラ不足)
def test_add_package_to_binder_param_error1(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_package_package02"
    binder_name = "test_add_package_binder02"
    # 前処理
    # パッケージ作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post("/binders/" + binder_name + "_owner/packages", json={})
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{ws}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 異常系(wsが不正)
def test_add_package_to_binder_param_error2(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    ws_err = "error_ws"
    package_name = "test_add_package_package03"
    binder_name = "test_add_package_binder03"
    # 前処理
    # パッケージ作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post(
        "/binders/" + binder_name + "_owner/packages", json={"ws": ws_err, "package_name": package_name}
    )
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict
    assert type(response_dict["detail"]) is list

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{ws}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 異常系 サーバーエラー
def test_add_package_to_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_package_package04"
    binder_name = "test_add_package_binder04"
    stdout = ""
    stderr = "test fail"
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.DEVELOP_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # パッケージを作成
    code, create_stdout, create_stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "create", package_name, "-v"]
    )
    assert code == 0

    # packageディレクトリに移動する
    rtc_dir_path = f"{dir_path}/{package_name}"
    os.chdir(rtc_dir_path)

    # パッケージ初期化
    code, init_stdout, init_stderr = start_process_return_string([mgr, "admin", "git_init", "-v"])
    assert code == 0

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str], stdin_str: Optional[str] = None) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.post("/binders/" + binder_name + "_owner/packages", json={"ws": ws, "package_name": package_name})
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理
    # パッケージ削除
    os.chdir(dir_path)
    code, del_stdout, del_stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert code == 0
    # バインダー削除
    delete_binder(binder_name)


# -------------------------------------------------
# PUT /binders/{name}/package/{package_name}
# 正常系
def test_update_package_in_binder_dev(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    name = "test_user_owner"
    binder_name = "test_user"
    package_name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200

    delete_binder(binder_name)


# 正常系
def test_update_package_in_binder_exec(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "exec"
    name = "test_user_owner"
    binder_name = "test_user"
    package_name = "test_project01"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", package_name])
    assert code == 0

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert del_code == 0

    delete_binder(binder_name)


def test_update_package_in_binder_param_error01(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー1 ws:NG name:OK package_name:OK
    ws = "ws_ng"
    name = "test_user_owner"
    package_name = "test_project01"
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 422


def test_update_package_in_binder_param_error02(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー2 ws:OK name:NG package_name:OK
    ws = "dev"
    name = "name_ng"
    package_name = "test_project01"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 500

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200


def test_update_package_in_binder_param_error03(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー3 ws:OK name:OK package_name:NG
    ws = "dev"
    name = "test_user_owner"
    package_name = "package_name_ng"
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 500


def test_update_package_in_binder_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 サーバーエラー
    ws = "dev"
    name = "test_user_owner"
    package_name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200


def test_update_package_in_binder_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # 正常系
    ws = "exec"
    name = "test_user_owner"
    package_name = "test_project01"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(
        ["wasanbon-admin.py", "repository", "clone", package_name]
    )
    assert code == 0

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put(f"/binders/{name}/package/{ws}/{package_name}")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert del_code == 0


# -------------------------------------------------
# POST /binders/{name}/rtcs
# 正常系(dev)
def test_add_rtc_to_binder_dev(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_rtc_package01"
    rtc_name = "TestIn_py"
    binder_name = "test_add_rtc_binder01"

    # 前処理
    # パッケージを作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # RTCをclone
    response = client.post(f"/{ws}/packages/{package_name}/rtcs/{rtc_name}/git/clone")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post(
        "/binders/" + binder_name + "_owner/rtcs", json={"ws": ws, "package_name": package_name, "rtc_name": rtc_name}
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{ws}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 正常系(exec)
def test_add_rtc_to_binder_exec(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "exec"
    package_name = "test_project01"
    rtc_name = "TestIn_py"
    binder_name = "test_add_rtc_binder01"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", package_name])
    assert code == 0

    # packageディレクトリに移動する
    rtc_dir_path = f"{config.EXECUTE_WORKSPACE_BASE_PATH}/{package_name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post(
        "/binders/" + binder_name + "_owner/rtcs", json={"ws": ws, "package_name": package_name, "rtc_name": rtc_name}
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict["message"]) is str

    # 後処理
    # パッケージ削除
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    # バインダー削除
    delete_binder(binder_name)


# 異常系 パラメタエラー (リクエストボディのパラメラ不足)
def test_add_rtc_to_binder_param_error1(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_rtc_package02"
    rtc_name = "TestIn_py"
    binder_name = "test_add_rtc_binder02"

    # 前処理
    # パッケージを作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # RTCをclone
    response = client.post(f"/{ws}/packages/{package_name}/rtcs/{rtc_name}/git/clone")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post(
        "/binders/" + binder_name + "_owner/rtcs", json={"package_name": package_name, "rtc_name": rtc_name}
    )
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{WS.dev}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 異常系(WSが不正)
def test_add_rtc_to_binder_param_error2(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    ws_err = "error_ws"
    package_name = "test_add_rtc_package03"
    rtc_name = "TestIn_py"
    binder_name = "test_add_rtc_binder03"

    # 前処理
    # パッケージを作成
    response = client.post(
        f"/{ws}/packages",
        json={"name": package_name},
    )
    assert response.status_code == 200

    # パッケージ初期化
    response = client.post(f"/{ws}/packages/{package_name}/git/init")
    assert response.status_code == 200

    # RTCをclone
    response = client.post(f"/{ws}/packages/{package_name}/rtcs/{rtc_name}/git/clone")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # メイン処理
    response = client.post(
        "/binders/" + binder_name + "_owner/rtcs",
        json={"ws": ws_err, "package_name": package_name, "rtc_name": rtc_name},
    )
    assert response.status_code == 422
    response_dict = response.json()
    assert "detail" in response_dict
    assert type(response_dict["detail"]) is list

    # 後処理
    # パッケージ削除
    response = client.delete(f"/{ws}/packages/{package_name}")
    assert response.status_code == 200
    # バインダー削除
    delete_binder(binder_name)


# 異常系 サーバーエラー
def test_add_rtc_to_binder_server_error(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    ws = "dev"
    package_name = "test_add_rtc_package04"
    rtc_name = "TestIn_py"
    binder_name = "test_add_rtc_binder04"
    stdout = ""
    stderr = "test fail"
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.DEVELOP_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # パッケージを作成
    code, create_stdout, create_stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "create", package_name, "-v"]
    )
    assert code == 0

    # packageディレクトリに移動する
    rtc_dir_path = f"{dir_path}/{package_name}"
    os.chdir(rtc_dir_path)

    # パッケージ初期化
    code, init_stdout, init_stderr = start_process_return_string([mgr, "admin", "git_init", "-v"])
    assert code == 0

    # RTCをclone
    code, clone_stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # バインダー作成
    code, crate_binder_stdout, crate_binder_stderr = start_process_return_string(
        [
            "wasanbon-admin.py",
            "binder",
            "create",
            "-v",
            "-u",
            binder_name,
            "-p",
            "test_pw",
            "-t",
            "YOUR_TOKEN",
        ]
    )
    assert code == 0 or code == 1

    # モックでコマンド実行時に失敗させる
    def mock_function(cmd: List[str], stdin_str: Optional[str] = None) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    response = client.post(
        "/binders/" + binder_name + "_owner/rtcs", json={"ws": ws, "package_name": package_name, "rtc_name": rtc_name}
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理
    # パッケージ削除
    os.chdir(dir_path)
    code, del_stdout, del_stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert code == 0
    # バインダー削除
    delete_binder(binder_name)


# -------------------------------------------------
# PUT /binders/{name}/rtc/{rtc_name}
def test_update_rtc_in_binder_dev(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 正常系
    ws = "dev"
    name = "test_user_owner"
    binder_name = "test_user"
    package_name = "test_project03"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200

    # バインダー削除
    delete_binder(binder_name)


def test_update_rtc_in_binder_exec(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 正常系
    ws = "exec"
    name = "test_user_owner"
    binder_name = "test_user"
    package_name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, stdout, clone_stderr = start_process_return_string(["wasanbon-admin.py", "repository", "clone", package_name])
    assert code == 0

    # packageディレクトリに移動する
    rtc_dir_path = f"{config.EXECUTE_WORKSPACE_BASE_PATH}/{package_name}"
    os.chdir(rtc_dir_path)

    # RTCをcloneする
    if sys.platform == "win32":
        mgr = "mgr.py"
    else:
        mgr = "./mgr.py"
    code, stdout, clone_stderr = start_process_return_string([mgr, "repository", "clone", rtc_name])
    assert code == 0

    # バインダー作成
    response = client.post(
        "/binders",
        json={"username": binder_name, "token": "YOUR_TOKEN"},
    )
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 200
    response_dict = response.json()
    assert "message" in response_dict
    assert type(response_dict.get("message")) is str

    # 後処理 packageを削除する
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert del_code == 0

    # バインダー削除
    delete_binder(binder_name)


def test_update_rtc_in_binder_param_error01(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー1 ws:NG name:OK package_name:OK rtc_name:OK
    ws = "ws_ng"
    name = "test_user_owner"
    package_name = "test_project01"
    rtc_name = "TestIn_py"
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 422


def test_update_rtc_in_binder_param_error02(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー2 ws:OK name:NG package_name:OK rtc_name:OK
    ws = "dev"
    name = "name_ng"
    package_name = "test_project01"
    rtc_name = "TestIn_py"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 500

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200


def test_update_rtc_in_binder_param_error03(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー3 ws:OK name:OK package_name:NG rtc_name:OK
    ws = "dev"
    name = "test_user_owner"
    package_name = "package_name_ng"
    rtc_name = "TestIn_py"
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 500


def test_update_rtc_in_binder_param_error04(client: TestClient) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 パラメタエラー4 ws:OK name:OK package_name:OK rtc_name:NG
    ws = "dev"
    name = "test_user_owner"
    package_name = "test_project01"
    rtc_name = "rtc_name_ng"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 500

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200


def test_update_rtc_in_binder_server_error01(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # 異常系 サーバーエラー
    ws = "dev"
    name = "test_user_owner"
    package_name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # packageをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/git/clone")
    assert response.status_code == 200

    # RTCをcloneする
    response = client.post("/" + ws + "/packages/" + package_name + "/rtcs/" + rtc_name + "/git/clone")
    assert response.status_code == 200

    def mock_function(cmd: List[str]) -> Tuple[int, str, str]:
        return (500, "", stderr)

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    response = client.delete("/" + ws + "/packages/" + package_name)
    assert response.status_code == 200


def test_update_rtc_in_binder_server_error02(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Wasanbon binderのテスト."""
    # 正常系
    ws = "exec"
    name = "test_user_owner"
    package_name = "test_project01"
    rtc_name = "TestIn_py"
    # モックでコマンド実行時に失敗させる
    stdout = ""
    stderr = "test fail"

    # 前処理
    # ワークスペースのディレクトリに移動する
    dir_path = config.EXECUTE_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    # packageをcloneする
    code, clone_stdout, clone_stderr = start_process_return_string(
        ["wasanbon-admin.py", "repository", "clone", package_name]
    )
    assert code == 0

    # packageディレクトリに移動する
    rtc_dir_path = f"{config.EXECUTE_WORKSPACE_BASE_PATH}/{package_name}"
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

    monkeypatch.setattr(binder_service, "start_process_return_string", mock_function)

    # テスト実行
    response = client.put(f"/binders/{name}/rtc/{ws}/{package_name}/{rtc_name}")
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}

    # 後処理 packageを削除する
    os.chdir(dir_path)
    del_code, stdout, stderr = start_process_return_string(
        ["wasanbon-admin.py", "package", "delete", "-r", package_name]
    )
    assert del_code == 0

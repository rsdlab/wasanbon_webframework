"""deploy Moduleのテストコード."""
import os
from typing import Any, Generator, List, Optional, Tuple

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from wasanbon_webframework.config.config import home_dir
from wasanbon_webframework.main import app
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services import common_service as com_service
from wasanbon_webframework.services import deploy_service as service
from wasanbon_webframework.services import packages_service as pkg_service
from wasanbon_webframework.services.process_util import start_process_return_string

exec = WS.exec
dev = WS.dev
TEST_PACKAGE = "exec_test_project01"
TEST_PACKAGE2 = "test_project01"
GIT_URL = "git@bd00git03.nes.sec.co.jp:p2417/development/packages/test_project01.git"
COMMIT_HASH = "dbc240373a5965eaa9704df3eb83710e2a0801de"

client = TestClient(app)


@pytest.fixture
def teardown_package() -> Generator[None, None, None]:
    """Wasanbon deployのセットアップ."""
    yield
    # 後片付けのみ
    pkg_service.delete_packages(TEST_PACKAGE)


@pytest.fixture
def setup_dummy_package() -> Generator[None, None, None]:
    """Wasanbon deployのセットアップ."""
    pkg_service.create_packages(exec, TEST_PACKAGE2)
    yield
    pkg_service.delete_packages(TEST_PACKAGE)


@pytest.fixture
def setup_error_package() -> Generator[None, None, None]:
    """Wasanbon deployのセットアップ."""
    pkg_service.create_packages(dev, TEST_PACKAGE)
    yield
    pkg_service.delete_packages(TEST_PACKAGE)


def get_git_remote_info() -> str:
    """Git remote -vを実行し結果を返却する."""
    command = ["git", "remote", "-v"]
    code, stdout, stderr = start_process_return_string(command)
    return stdout


# POST /{ws}/packages/deploy
# 正常系(execにパッケージ作成なし⇒deploy)
def test_post_packages_deploy(teardown_package: Any) -> None:
    # 正常系(execにパッケージ作成なし⇒deploy)
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )

    assert response.status_code == 200
    assert "Deployment to Execute workspace completed." in response.json()["message"]

    # テストパッケージが作成されていることを確認
    test_paackage_dir = os.path.join(com_service.get_basepath(exec), TEST_PACKAGE)
    assert os.path.isdir(test_paackage_dir)

    os.chdir(test_paackage_dir)
    stdout = get_git_remote_info()
    assert GIT_URL in stdout
    os.chdir(home_dir)


def test_post_packages_deploy2(setup_dummy_package: Any) -> None:
    # 正常系(execにパッケージ作成しdeploy)
    """Wasanbon deployのテスト."""
    # ダミーパッケージが作成されていることを確認
    dummy_paackage_dir = os.path.join(com_service.get_basepath(exec), TEST_PACKAGE2)
    assert os.path.isdir(dummy_paackage_dir)

    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )

    assert response.status_code == 200
    assert "Deployment to Execute workspace completed." in response.json()["message"]

    # ダミーパッケージが削除されていることを確認
    assert not os.path.isdir(dummy_paackage_dir)
    # テストパッケージが作成されていることを確認
    test_paackage_dir = os.path.join(com_service.get_basepath(exec), TEST_PACKAGE)
    assert os.path.isdir(test_paackage_dir)

    os.chdir(test_paackage_dir)
    stdout = get_git_remote_info()
    assert GIT_URL in stdout
    os.chdir(home_dir)


def test_post_packages_deploy_error(setup_error_package: Any) -> None:
    # 異常系(devに重複するパッケージ作成しdeploy)
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )

    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_packages_deploy_param_error() -> None:
    # 異常系(ws:NG)
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{dev}/packages/deploy",
        json={"rts_git_url": "rts_git_url", "commit_hash": "commit_hash"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Develop workspace cannot be deployed"}


def test_post_packages_deploy_param_error2() -> None:
    # 異常系(rts_git_url:NG(空文字))
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": "", "commit_hash": "commit_hash"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_packages_deploy_param_error3() -> None:
    # 異常系(rts_git_url:NG(未指定))
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"commit_hash": "commit_hash"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_packages_deploy_param_error4() -> None:
    # 異常系(commit_hash:NG(空文字))
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": "rts_git_url", "commit_hash": ""},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_packages_deploy_param_error5() -> None:
    # 異常系(commit_hash:NG(未指定))
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": "rts_git_url"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_packages_deploy_url_error() -> None:
    # 異常系(rts_git_url::正しいGitのURLではない場合)
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": "rts_git_url", "commit_hash": "commit_hash"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": "", "stderr": "Could not get package name from URL"}}


def test_post_packages_deploy_del_package_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(パッケージ削除失敗) モックでコマンド実行時に失敗させる
    """Wasanbon deployのテスト."""
    stdout = "del package out"
    stderr = "del package error"

    def mock_function(ws: WS) -> Tuple[int, Optional[str], str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "del_exec_package", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_create_package_error(monkeypatch: MonkeyPatch) -> None:
    # 異常系(パッケージ作成エラー)
    """Wasanbon deployのテスト."""
    stdout = "create package out"
    stderr = "create package error"

    def mock_function(pkg_name: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "create_package", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_init_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(init失敗)　モックでコマンド実行時に失敗させる
    """Wasanbon deployのテスト."""
    stdout = "git init out"
    stderr = "git init error"

    def mock_function(pkg_name: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "git_init", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_remote_add_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(remote add失敗)　モックでコマンド実行時に失敗させる
    """Wasanbon deployのテスト."""
    stdout = "git remote add out"
    stderr = "git remote add error"

    def mock_function(pkg_name: str, url: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "git_remote_add", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_fetch_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(fetch失敗)　モックでコマンド実行時に失敗させる
    """Wasanbon deployのテスト."""
    stdout = "git fetch out"
    stderr = "git fetch error"

    def mock_function(pkg_name: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "git_fetch", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_checkout_error(teardown_package: Any) -> None:
    # 異常系(checkout失敗)
    """Wasanbon deployのテスト."""
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": "ngcommithash"},
    )
    assert response.status_code == 500
    assert "detail" in response.json()


def test_post_packages_deploy_edit_yaml_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(setting.yamlの編集失敗)
    """Wasanbon deployのテスト."""
    stdout = "edit setting yaml out"
    stderr = "edit setting yaml error"

    def mock_function(pkg_name: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "edit_setting_yaml", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_rtc_clone_error(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 異常系(rtc clone失敗)
    """Wasanbon deployのテスト."""
    stdout = "rtc clone out"
    stderr = "rtc clone error"

    def mock_function(clone_list: List[str], pkg_name: str) -> Tuple[int, str, str]:
        return (1, stdout, stderr)

    monkeypatch.setattr(service, "rtc_clone", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": {"stdout": stdout, "stderr": stderr}}


def test_post_packages_deploy_rtc_list_empty(teardown_package: Any, monkeypatch: MonkeyPatch) -> None:
    # 正常系(rtc clone一覧が空の場合)
    """Wasanbon deployのテスト."""
    # RTCのリストを空になるように返却
    def mock_function(pkg_name: str, ip: str) -> Tuple[List[str], List[str]]:
        return ([], [])

    monkeypatch.setattr(service, "get_rtc_list", mock_function)

    # テスト実行
    response = client.post(
        f"/deploy/{exec}/packages/deploy",
        json={"rts_git_url": GIT_URL, "commit_hash": COMMIT_HASH},
    )
    assert response.status_code == 200
    assert "Deployment to Execute workspace completed." in response.json()["message"]

    # テストパッケージが作成されていることを確認
    test_paackage_dir = os.path.join(com_service.get_basepath(exec), TEST_PACKAGE)
    assert os.path.isdir(test_paackage_dir)

    os.chdir(test_paackage_dir)
    stdout = get_git_remote_info()
    assert GIT_URL in stdout
    os.chdir(home_dir)

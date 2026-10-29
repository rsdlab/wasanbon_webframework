"""ITケース02のテストコード."""
import os
import json
import base64
import shutil
from typing import Any, Generator

import stat
import pytest
import requests
import yaml

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services.packages_service import delete_packages
from wasanbon_webframework.services.process_util import start_process_return_string
from integration_tests.it_config import localhost_ip_address, server_port

# パラメタ定義
url = f"http://{localhost_ip_address}:{server_port}"
user_pass = "admin:admin"
encoded = base64.b64encode(user_pass.encode()).decode()
header = {"Authorization" : f"Basic {encoded}"}

dev = WS.dev
name = "IT_user_owner"
package_name = "test_project02"
rtc_name = "TestIn_py"

binder_path = f"{home_dir}/.wasanbon/binder/{name}/wasanbon_binder.git"
dev_package_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name}"
dev_rtc_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name}/rtc/{rtc_name}"

commit_data = {"comment": "add package and rtc"}
binder_data = {"username": "IT_user", "token": "YOUR_TOKEN"}
dev_package_data = {"ws": dev, "package_name": package_name}
dev_package_rtc_data = {"ws": dev, "package_name": package_name, "rtc_name": rtc_name}


def _test_04_1() -> None:
    """試験ケース04-1(正常系)."""
    # 1-1 テスト実行
    response = requests.post(f"{url}/binders/", data=json.dumps(binder_data), headers=header)

    # check
    assert response.status_code == 200
    assert os.path.exists(binder_path)
    os.chdir(binder_path)
    code, stdout, stderr = start_process_return_string(["git", "fetch"])
    assert code == 0
    os.chdir(home_dir)


def _test_04_2() -> None:
    """試験ケース04-2(正常系)."""
    # 2-1 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/git/clone", headers=header)

    # check
    assert response.status_code == 200
    assert os.path.exists(dev_package_path)

    # 2-2 テスト実行
    response = requests.post(f"{url}/binders/{name}/rtcs/", data=json.dumps(dev_package_rtc_data), headers=header)

    # check
    assert response.status_code == 200
    assert os.path.exists(dev_package_path)
    with open(f"{home_dir}/.wasanbon/binder/IT_user_owner/wasanbon_binder.git/rtcs/examples.yaml", "r") as yml:
        yaml_data = yaml.safe_load(yml)
        rtc_name in yaml_data


def _test_04_3() -> None:
    """試験ケース04-3(正常系)."""
    # 3-1 テスト実行
    os.chdir(dev_rtc_path)
    code, stdout, stderr = start_process_return_string(["git", "checkout", "-b", "test_branch"])

    # check
    assert code == 0
    os.chdir(home_dir)

    # 3-2 テスト実行
    response = requests.put(f"{url}/binders/{name}/rtc/{dev}/{package_name}/{rtc_name}", headers=header)

    # check
    assert response.status_code == 200
    with open(f"{home_dir}/.wasanbon/binder/IT_user_owner/wasanbon_binder.git/rtcs/examples.yaml", "r") as yml:
        yaml_data = yaml.safe_load(yml)
        assert "test_branch" in list(yaml_data[rtc_name]["platform"].values())


def _test_04_4() -> None:
    """試験ケース04-4(正常系)."""
    # 4-2 テスト実行
    response = requests.post(f"{url}/binders/{name}/packages/", data=json.dumps(dev_package_data), headers=header)

    # check
    assert response.status_code == 200
    with open(f"{home_dir}/.wasanbon/binder/IT_user_owner/wasanbon_binder.git/packages/examples.yaml", "r") as yml:
        yaml_data = yaml.safe_load(yml)
        rtc_name in yaml_data


def _test_04_5() -> None:
    """試験ケース04-5(正常系)."""
    # 5-1 テスト実行
    os.chdir(dev_package_path)
    code, stdout, stderr = start_process_return_string(["git", "checkout", "-b", "test_branch"])

    # check
    assert code == 0
    os.chdir(home_dir)

    # 5-2 テスト実行
    response = requests.put(f"{url}/binders/{name}/package/{dev}/{package_name}", headers=header)

    # check
    assert response.status_code == 200
    with open(f"{binder_path}/packages/examples.yaml", "r") as yml:
        yaml_data = yaml.safe_load(yml)
        assert "test_branch" in list(yaml_data[package_name]["platform"].values())


def _test_04_6() -> None:
    """試験ケース04-6(正常系)."""
    # 6-1 テスト実行
    response = requests.post(f"{url}/binders/{name}/commit", data=json.dumps(commit_data), headers=header)

    # check
    assert response.status_code == 200
    os.chdir(binder_path)
    code, stdout, stderr = start_process_return_string(["git", "log", "-1"])
    assert commit_data["comment"] in stdout
    os.chdir(home_dir)

    # 6-2 テスト実行
    response = requests.post(f"{url}/binders/{name}/push", data=json.dumps(commit_data), headers=header)

    # check
    assert response.status_code == 500
    os.chdir(home_dir)


def test04() -> None:
    _test_04_1()
    _test_04_2()
    _test_04_3()
    _test_04_4()
    _test_04_5()
    _test_04_6()

    os.chdir(home_dir)
    delete_packages(package_name)
    try:
        for root, dirs, files in os.walk(f"{home_dir}/.wasanbon/binder/IT_user_owner"):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(f"{home_dir}/.wasanbon/binder/IT_user_owner")
    except Exception as e:
        pass

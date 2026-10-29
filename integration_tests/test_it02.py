"""ITケース02のテストコード."""
import json
import logging
import os
import re
import sys
import stat
import base64
import shutil
import zipfile
from time import sleep
from typing import Any, Generator, List, Tuple

import psutil
import pytest
import requests
from fastapi import FastAPI, Request, Response

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services.packages_service import delete_packages
from wasanbon_webframework.services.process_util import start_background_process_return_string, start_process_return_string
from wasanbon_webframework.services.wasanbon_util import _generate_wasanbon_admin_command
from wasanbon_webframework.services import execution_service as ex_service
from integration_tests.it_config import localhost_ip_address, server_port

logger = logging.getLogger(__name__)

# パラメタ定義
url = f"http://{localhost_ip_address}:{server_port}"
user_pass = "admin:admin"
encoded = base64.b64encode(user_pass.encode()).decode()
header = {"Authorization" : f"Basic {encoded}"}
headers = {"Authorization" : f"Basic {encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}

dev = WS.dev
exec = WS.exec
package_name = "test_project01"
exec_package_name = "exec_test_project01"
rtc_list = ["TestIn_cpp", "TestOut_cpp", "TestIn_py"]

binder_path = f"{home_dir}/.wasanbon/binder/IT_user_owner/wasanbon_binder.git/"
dev_package_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name}"
dev_rtc_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name}/rtc/{rtc_list[2]}"
exec_package_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{package_name}"
exec_rtc_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{package_name}/rtc"
deploy_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{exec_package_name}"

deploy_data = {
    "rts_git_url": "git@bd00git03.nes.sec.co.jp:p2417/development/packages/test_project01.git",
    "commit_hash": "3b2cebf879db4f4795ecdf6a84125ac60b97fa2b",
}
binder_data = {"username": "IT_user", "token": "YOUR_TOKEN"}


def check_process(proc_name: str) -> bool:
    """プロセスのチェックを行う."""
    return ex_service.is_process(proc_name)


def _test_02_1() -> None:
    """試験ケース02-1(正常系)."""
    # 1-1 テスト実行
    response = requests.post(f"{url}/binders/", data=json.dumps(binder_data), headers=header)

    assert response.status_code == 200
    assert os.path.exists(binder_path)
    os.chdir(binder_path)
    code, stdout, stderr = start_process_return_string(["git", "fetch"])
    assert code == 0
    os.chdir(home_dir)


def _test_02_2() -> None:
    """試験ケース02-2(正常系)."""
    # 2-1 テスト実行
    response = requests.get(f"{url}/binders/packages", headers=header)

    # check
    assert response.status_code == 200
    json_data = response.json()
    assert len(list(json_data["packages"])) > 0

    # 2-2 テスト実行
    response = requests.get(f"{url}/binders/rtcs", headers=header)

    # check
    assert response.status_code == 200
    json_data = response.json()
    assert len(list(json_data["rtcs"])) > 0


def _test_02_3() -> None:
    """試験ケース02-3(正常系)."""
    # 3-1 テスト実行
    response = requests.get(f"{url}/{dev}/packages", headers=headers)

    # check
    assert response.status_code == 200
    json_data = response.json()
    assert len(list(json_data["packages"])) == 0

    # 3-2 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/git/clone", headers=header)

    # check
    assert response.status_code == 200
    assert os.path.exists(dev_package_path)

    # 3-3 テスト実行
    response = requests.get(f"{url}/{dev}/packages", headers=headers)

    # check
    assert response.status_code == 200
    json_data = response.json()
    package_list = list(json_data["packages"])
    assert len(package_list) == 1
    assert package_name in package_list[0].keys()

    # 3-4 テスト実行
    response = requests.get(f"{url}/{dev}/packages/{package_name}/rtcs", headers=headers)

    # check
    assert response.status_code == 200
    json_data = response.json()
    response_rtc_list = list(json_data["rtcs"])
    assert len(response_rtc_list) == 2
    response_key_list = [response_rtc_list[0].keys(), response_rtc_list[1].keys()]
    assert {rtc_list[0]} in response_key_list
    assert {rtc_list[1]} in response_key_list

    # 3-5 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/rtcs/{rtc_list[2]}/git/clone", headers=header)

    # check
    assert response.status_code == 200
    assert os.path.exists(dev_rtc_path)

    # 3-6 テスト実行
    response = requests.get(f"{url}/{dev}/packages/{package_name}/rtcs", headers=headers)

    # check
    assert response.status_code == 200
    json_data = response.json()
    response_rtc_list = list(json_data["rtcs"])
    assert len(response_rtc_list) == 3
    response_key_list = [list(response_rtc_list[0].keys()), list(response_rtc_list[1].keys()), list(response_rtc_list[2].keys())]
    for rtc in rtc_list:
        assert rtc in [response_key_list[0][0], response_key_list[1][0], response_key_list[2][0]]


def _test_02_4() -> None:
    """試験ケース02-4(正常系)."""
    # 4-1 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/rtcs/{rtc_list[0]}/build", headers=header)

    # check
    assert response.status_code == 200
    file_list = os.listdir(f"{dev_package_path}/rtc/{rtc_list[0]}")
    build_folder = [i for i in file_list if "build" in i]
    assert len(build_folder) == 1

    # 4-2 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/rtcs/{rtc_list[1]}/build", headers=header)

    # check
    assert response.status_code == 200
    file_list = os.listdir(f"{dev_package_path}/rtc/{rtc_list[1]}")
    build_folder = [i for i in file_list if "build" in i]
    assert len(build_folder) == 1


def _test_02_5() -> None:
    """試験ケース02-5(正常系)."""
    # 5-1 テスト実行
    response = requests.post(f"{url}/nameserver/start", headers=headers)

    # 5-2 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name}/rts/run", headers=header)

    # check
    assert response.status_code == 200
    assert check_process("rtcd") or check_process("/usr/bin/rtcd_python3")

    # 5-3 テスト実行
    response = requests.get(f"{url}/{dev}/packages/{package_name}/rts/status", headers=header)

    # check
    assert response.status_code == 200
    json_data = response.json()
    successful_rtcs_list = list(json_data["successful_RTCs"])
    connect_testin_cpp = r"TestIn_cpp(.*).rtc"
    connect_testout_cpp = r"TestOut_cpp(.*).rtc"
    if successful_rtcs_list[0].startswith("TestOut"):
        for rtc in successful_rtcs_list:
            assert "Active" in rtc
        assert re.search(connect_testin_cpp, successful_rtcs_list[0]) != None
        assert re.search(connect_testout_cpp, successful_rtcs_list[1]) != None
    else:
        for rtc in successful_rtcs_list:
            assert "Active" in rtc
        assert re.search(connect_testout_cpp, successful_rtcs_list[0]) != None
        assert re.search(connect_testin_cpp, successful_rtcs_list[1]) != None

    # 5-4 テスト実行
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name}/rts/terminate/", headers=header)

    # check
    assert response.status_code == 200
    assert not check_process("rtcd") or not check_process("/usr/bin/rtcd_python3")

    # 5-5 テスト実行
    response = requests.get(f"{url}/{dev}/packages/{package_name}/rts/logs", headers=header)

    # check
    assert response.status_code == 200
    contentType = response.headers["Content-Type"]
    contentDisposition = response.headers["Content-Disposition"]
    ATTRIBUTE = "filename="
    file_name = contentDisposition[contentDisposition.find(ATTRIBUTE) + len(ATTRIBUTE) :]

    save_file_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{file_name}"
    save_file_dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/test_log"

    os.chdir(DEVELOP_WORKSPACE_BASE_PATH)
    with open(save_file_path, "wb") as save_file:
        save_file.write(response.content)
    with zipfile.ZipFile(file_name) as zf:
        os.mkdir(save_file_dir_path)
        os.chdir(save_file_dir_path)
        zf.extractall()
    assert set(os.listdir(save_file_dir_path)) == set(os.listdir(f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name}/log"))

    # 5-6 テスト実行
    response = requests.post(f"{url}/nameserver/stop", headers=headers)

    # 後処理
    os.chdir(home_dir)
    os.remove(save_file_path)


def _test_02_6() -> None:
    """試験ケース02-6(正常系)."""
    # 6-1 テスト実行
    response = requests.get(f"{url}/{exec}/packages", headers=header)

    # check
    assert response.status_code == 200
    json_data = response.json()
    assert len(list(json_data["packages"])) == 0

    # 6-2 テスト実行
    response = requests.post(f"{url}/deploy/{exec}/packages/deploy", data=json.dumps(deploy_data), headers=header)

    # check
    assert response.status_code == 200
    os.chdir(deploy_path)
    code, stdout, stderr = start_process_return_string(["git", "log", "-1"])
    assert code == 0
    assert deploy_data["commit_hash"] in stdout
    assert os.path.exists(deploy_path)
    assert os.path.exists(f"{deploy_path}/rtc/{rtc_list[0]}")
    assert os.path.exists(f"{deploy_path}/rtc/{rtc_list[1]}")


def _test_02_7() -> None:
    """試験ケース02-7(正常系)."""
    # 7-1 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rtcs/{rtc_list[0]}/build", headers=header)

    # check
    assert response.status_code == 200
    file_list = os.listdir(f"{deploy_path}/rtc/{rtc_list[0]}")
    build_folder = [i for i in file_list if "build" in i]
    assert len(build_folder) == 1

    # 7-2 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rtcs/{rtc_list[1]}/build", headers=header)

    # check
    assert response.status_code == 200
    file_list = os.listdir(f"{deploy_path}/rtc/{rtc_list[1]}")
    build_folder = [i for i in file_list if "build" in i]
    assert len(build_folder) == 1


def _test_02_8() -> None:
    """試験ケース02-8(正常系)."""
    # 8-1 テスト実行
    response = requests.post(f"{url}/nameserver/start", headers=headers)

    # 8-2 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/run", headers=header)
    sleep(10)

    # check
    assert response.status_code == 200
    assert check_process("rtcd") or check_process("/usr/bin/rtcd_python3")

    # 8-3 テスト実行
    response = requests.get(f"{url}/{exec}/packages/{exec_package_name}/rts/status", headers=header)

    # check
    assert response.status_code == 200
    json_data = response.json()
    successful_rtcs_list = list(json_data["successful_RTCs"])
    connect_testin_cpp = r"TestIn_cpp(.*).rtc"
    connect_testout_cpp = r"TestOut_cpp(.*).rtc"
    if successful_rtcs_list[0].startswith("TestOut"):
        for rtc in successful_rtcs_list:
            assert "Active" in rtc
        assert re.search(connect_testin_cpp, successful_rtcs_list[0]) != None
        assert re.search(connect_testout_cpp, successful_rtcs_list[1]) != None
    else:
        for rtc in successful_rtcs_list:
            assert "Active" in rtc
        assert re.search(connect_testout_cpp, successful_rtcs_list[0]) != None
        assert re.search(connect_testin_cpp, successful_rtcs_list[1]) != None

    # 8-4 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/terminate/", headers=header)
    sleep(10)

    # check
    assert response.status_code == 200
    assert not check_process("rtcd") or not check_process("/usr/bin/rtcd_python3")

    # 8-5 テスト実行
    response = requests.get(f"{url}/{exec}/packages/{exec_package_name}/rts/logs", headers=header)

    # check
    assert response.status_code == 200
    contentType = response.headers["Content-Type"]
    contentDisposition = response.headers["Content-Disposition"]
    ATTRIBUTE = "filename="
    file_name = contentDisposition[contentDisposition.find(ATTRIBUTE) + len(ATTRIBUTE) :]

    save_file_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{file_name}"
    save_file_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/test_log"

    os.chdir(EXECUTE_WORKSPACE_BASE_PATH)
    with open(save_file_path, "wb") as save_file:
        save_file.write(response.content)
    with zipfile.ZipFile(file_name) as zf:
        os.mkdir(save_file_dir_path)
        os.chdir(save_file_dir_path)
        zf.extractall()
    assert set(os.listdir(save_file_dir_path)) == set(
        os.listdir(f"{EXECUTE_WORKSPACE_BASE_PATH}/{exec_package_name}/log")
    )

    # 8-6 テスト実行
    response = requests.post(f"{url}/nameserver/stop", headers=headers)

    # 後処理
    os.chdir(home_dir)
    os.remove(save_file_path)


def test02() -> None:
    _test_02_1()
    _test_02_2()
    _test_02_3()
    _test_02_4()
    _test_02_5()
    os.chdir(home_dir)
    _test_02_6()
    _test_02_7()
    _test_02_8()
    os.chdir(home_dir)

    # 後処理
    delete_packages(package_name)
    delete_packages(exec_package_name)
    shutil.rmtree(f"{DEVELOP_WORKSPACE_BASE_PATH}/test_log")
    shutil.rmtree(f"{EXECUTE_WORKSPACE_BASE_PATH}/test_log")
    try:
        for root, dirs, files in os.walk(f"{home_dir}/.wasanbon/binder/IT_user_owner"):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(f"{home_dir}/.wasanbon/binder/IT_user_owner")
    except Exception as e:
        logger.error("removed fail IT_user_owner")

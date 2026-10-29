"""ITケース02のテストコード."""
import base64
import json
import logging
import os
import re
from multiprocessing import Process

import requests
import yaml

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.models.ws import WS
from wasanbon_webframework.services import execution_service as ex_service
from wasanbon_webframework.services.packages_service import delete_packages
from wasanbon_webframework.services.process_util import start_background_process_return_string, start_process_return_string
from wasanbon_webframework.services.wasanbon_util import _generate_wasanbon_admin_command
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
package_name1 = "test_project01"
package_name2 = "test_project02"
package_name3 = "test_project03"
exec_package_name = "exec_test_project01"
rtc_list = ["TestIn_cpp", "TestOut_cpp", "TestIn_py"]

deploy_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{exec_package_name}"

old_deploy_data = {
    "rts_git_url": "git@bd00git03.nes.sec.co.jp:p2417/development/packages/test_project01.git",
    "commit_hash": "6a4c96b13ac7ef85c37c842e689f65fe16090d81",
}
deploy_data = {
    "rts_git_url": "https://github.com/wasanbon/test_project01.git",
    "commit_hash": "be56a3f592dffdbde58d4f9b7ce7bb034bab82d3",
}


def check_process(proc_name: str) -> bool:
    """プロセスのチェックを行う."""
    return ex_service.is_process(proc_name)


def test_05_1() -> None:
    """試験ケース05-1(異常系)."""
    # 1-0-1 テスト実行
    user_ng_pass = "ng_user:admin"
    user_ng_encoded = base64.b64encode(user_ng_pass.encode()).decode()
    user_ng_header = {"Authorization" : f"Basic {user_ng_encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}
    response = requests.get(f"{url}/version", headers=user_ng_header)

    assert response.status_code == 401

    # 1-0-2 テスト実行
    user_pass_ng = "admin:ng_pass"
    pass_ng_encoded = base64.b64encode(user_pass_ng.encode()).decode()
    pass_ng_header = {"Authorization" : f"Basic {pass_ng_encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}
    response = requests.get(f"{url}/version", headers=pass_ng_header)

    assert response.status_code == 401

    with open(f'{home_dir}/.wasanbon-webframework/user_info.yml', 'r') as yml:
        base_yaml_data = yaml.safe_load(yml)

    # 1-1-1 テスト実行
    os.remove(f"{home_dir}/.wasanbon-webframework/user_info.yml")
    response = requests.get(f"{url}/version", headers=headers)
    assert response.status_code == 500
    assert " No such file or directory:" in response.content.decode()

    # 1-1-2 テスト実行
    with open(f'{home_dir}/.wasanbon-webframework/user_info.yml', 'w') as yml:
        yml.write("NG_user_info")
    response = requests.get(f"{url}/version", headers=headers)
    assert response.status_code == 500
    assert "failed to get user info" in response.content.decode()

    # 1-2-1 テスト実行
    with open(f'{home_dir}/.wasanbon-webframework/user_info.yml', 'w') as yml:
        yml_write_data = {"user1":"user1_password", "user2":"user2_password"}
        yaml.dump(yml_write_data, yml)
    user1_pass = "user1:user1_password"
    user1_pass_encoded = base64.b64encode(user1_pass.encode()).decode()
    user1_pass_header = {"Authorization" : f"Basic {user1_pass_encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}
    response = requests.get(f"{url}/version", headers=user1_pass_header)

    assert response.status_code == 200

    user2_pass = "user2:user2_password"
    user2_pass_encoded = base64.b64encode(user2_pass.encode()).decode()
    user2_pass_header = {"Authorization" : f"Basic {user2_pass_encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}
    response = requests.get(f"{url}/version", headers=user2_pass_header)

    assert response.status_code == 200

    # 後処理
    with open(f'{home_dir}/.wasanbon-webframework/user_info.yml', 'w') as yml:
        base_yaml_data  = {'admin': 'admin'}
        yaml.dump(base_yaml_data, yml)


def test_05_2_1_to_05_2_3() -> None:
    """試験ケース02-2(正常系)."""

    # 2-1-1 テスト実行
    response = requests.post(f"{url}/deploy/{exec}/packages/deploy", data=json.dumps(old_deploy_data), headers=header)

    assert response.status_code == 200
    os.chdir(deploy_path)
    code, stdout, stderr = start_process_return_string(["git", "log", "-1"])
    assert code == 0
    assert old_deploy_data["commit_hash"] in stdout
    assert os.path.exists(f"{deploy_path}")
    assert os.path.exists(f"{deploy_path}/rtc/{rtc_list[0]}")
    assert os.path.exists(f"{deploy_path}/rtc/{rtc_list[1]}")
    os.chdir(home_dir)

    # 2-1-2 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/build", headers=header)

    assert response.status_code == 500
    pattern = r"Build RTC (.*) * False"
    assert re.search(pattern, response.json()["detail"]["stdout"]) is not None

    # 2-1-3 テスト実行
    response = requests.post(f"{url}/deploy/{exec}/packages/deploy", data=json.dumps(deploy_data), headers=header)
    assert response.status_code == 200

    # 2-1-4 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/build", headers=header)

    assert response.status_code == 200
    file_list = os.listdir(f"{deploy_path}/bin")
    assert len(file_list) > 0

    # 2-2-1 テスト実行
    response = requests.post(f"{url}/nameserver/start", headers=headers)

    # 2-2-2 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/run", headers=header)

    assert response.status_code == 200
    assert check_process("rtcd") or check_process("/usr/bin/rtcd_python3")

    # 2-2-3 テスト実行
    response = requests.get(f"{url}/{exec}/packages/{exec_package_name}/rts/status", headers=header)

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

    # 2-2-4 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/run", headers=header)

    assert response.status_code == 200
    assert check_process("rtcd") or check_process("/usr/bin/rtcd_python3")

    # 2-2-5 テスト実行
    response = requests.get(f"{url}/{exec}/packages/{exec_package_name}/rts/status", headers=header)

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

    # 2-3-1 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/terminate", headers=header)

    assert response.status_code == 200
    assert not check_process("rtcd") or not check_process("/usr/bin/rtcd_python3")

    # 2-3-2 テスト実行
    response = requests.post(f"{url}/{exec}/packages/{exec_package_name}/rts/terminate", headers=header)

    assert response.status_code == 200
    assert not check_process("rtcd") or not check_process("/usr/bin/rtcd_python3")

    # 2-3-3 テスト実行
    response = requests.post(f"{url}/nameserver/stop", headers=headers)

    # 後処理
    delete_packages(exec_package_name)

def test_05_2_4() -> None:
    # 2-4-1 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name3}/git/clone", headers=header)

    assert response.status_code == 200
    assert os.path.exists(f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name3}")

    # 2-4-2 テスト実行
    req_body = {"name": package_name3}
    response = requests.post(f"{url}/{dev}/packages/", headers=header, data=json.dumps(req_body))

    assert response.status_code == 500
    assert "package in workspace.yaml already" in response.json()["detail"]["stdout"]

    # 2-4-3 テスト実行
    response = requests.delete(f"{url}/{dev}/packages/{package_name3}", headers=header)

    assert response.status_code == 200
    file_list = os.listdir(f"{DEVELOP_WORKSPACE_BASE_PATH}")
    assert package_name3 not in file_list

    # 2-4-4 テスト実行
    req_body = {"name": package_name3}
    response = requests.post(f"{url}/{dev}/packages/", headers=header, data=json.dumps(req_body))

    assert response.status_code == 200
    file_list = os.listdir(f"{DEVELOP_WORKSPACE_BASE_PATH}")
    assert package_name3 in file_list

    # 2-4-5 テスト実行
    response = requests.post(f"{url}/{dev}/packages/{package_name3}/git/clone", headers=header)

    assert response.status_code == 500
    assert "package in workspace.yaml already" in response.json()["detail"]["stdout"]

    # 後処理
    response = requests.delete(f"{url}/{dev}/packages/{package_name3}", headers=header)
    assert response.status_code == 200


def clone_test(expect_code: int, expect_msg: str) -> None:
    """cloneのAPIを処理する.

    Args:
        expect_code (int): 期待ステータスコード
        expect_msg (str): 期待レスポンスメッセージ
    """
    response = requests.post(f"{url}/{dev}/packages/{package_name2}/git/clone", headers=header)
    assert response.status_code == expect_code
    if expect_code == 200:
        assert expect_msg in response.json()["message"]
    else:
        assert expect_msg in response.json()["detail"]["stdout"]


def test_05_2_5() -> None:
    # 2-5-1 テスト実行
    p1 = Process(target=clone_test, args=(200, "Success"))
    p2 = Process(target=clone_test, args=(500, "package in workspace.yaml already"))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # 後処理
    response = requests.delete(f"{url}/{dev}/packages/{package_name2}", headers=header)
    assert response.status_code == 200

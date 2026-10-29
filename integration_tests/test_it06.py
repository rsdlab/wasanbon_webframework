"""ITケース06のテストコード."""

import base64
import glob
import json
import os
import pytest
import shutil
import stat
import yaml
import requests
import zipfile
from typing import Any, Generator, Tuple

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.services import execution_service as ex_service
from wasanbon_webframework.services.process_util import start_process_return_string, start_background_process_return_string
from integration_tests.it_config import localhost_ip_address, localhost_ip_address_mac, localhost_ip_address_linux, server_port
from wasanbon_webframework.services.wasanbon_util import _generate_wasanbon_admin_command
from wasanbon_webframework.models.ws import WS

# ip = localhost_ip_address_mac
ip = localhost_ip_address
# ip2 = localhost_ip_address_mac
ip2 = localhost_ip_address_linux
url = f"http://{ip}:{server_port}"
url2 = f"http://{ip2}:{server_port}"

user_pass = "admin:admin"
encoded = base64.b64encode(user_pass.encode()).decode()
headers = {"Authorization" : f"Basic {encoded}", "Cache-Control": "no-cache", "Pragma": "no-cache", "content-type": "application/json"}

binder_git = "wasanbon_binder"
binder_base_dir = f"{home_dir}/.wasanbon/binder"
binder_user = "IT_user"
binder_dir = f"{binder_base_dir}/{binder_user}_owner/{binder_git}.git/"
binder_data = {"username": binder_user, "token": "YOUR_TOKEN" }

package_name2 = "test_package2"
package_data = {"name": package_name2 }
git_url = "git@bd00git03.nes.sec.co.jp:p2417/development/packages/group_for_test/package_to_test2.git"
git_data = { "url":git_url}
comment = "add RTCs"
comment2 = "add RTSProfile"
commit_data = {"comment": comment}

rtc_test_in_cpp = "TestIn_cpp"
rtc_test_out_cpp  = "TestOut_cpp"
rtc_test_in_py = "TestIn_py"
rtc_test_out_py = "TestOut_py"

exec_package_name = "exec_package_to_test2"

@pytest.fixture
def setup_clean_package() -> Generator[None, None, None]:
    """前後処理 開始前後にバインダーディレクトリ、パッケージを削除する."""
    requests.delete(f"{url}/{WS.dev}/packages/{package_name2}", headers=headers)
    del_binder_dir()
    response = requests.post(f"{url}/nameserver/stop", headers=headers)
    response = requests.post(f"{url2}/nameserver/stop", headers=headers)
    yield
    requests.delete(f"{url}/{WS.dev}/packages/{package_name2}", headers=headers)
    del_binder_dir()
    response = requests.post(f"{url}/nameserver/stop", headers=headers)
    response = requests.post(f"{url2}/nameserver/stop", headers=headers)


#------------------------------------------------------------
# チェック／補助関数
def get_git_remote_info() -> str:
    """git remote -vを実行し結果を返却する."""
    command = ["git", "remote", "-v"]
    code, stdout, stderr = start_process_return_string(command)
    return stdout


def del_master_bransh() -> Tuple[int, str, str]:
    """pushするためにmasterブランチを削除しておく."""
    command = [ "git", "push", "origin", "--delete", "master",]
    code, stdout, stderr =  start_process_return_string(command)
    return code, stdout, stderr


def get_git_log() -> str:
    """git logの取得を行う."""
    command = [ "git", "log", "-n", "1", ]
    code, stdout, stderr =  start_process_return_string(command)
    return stdout


def git_pull() -> str:
    """pushするためにmasterブランチを削除しておく."""
    command = [ "git", "pull", "origin", "master",]
    code, stdout, stderr =  start_process_return_string(command)
    return stdout


def git_commit_hash() -> str:
    """git コミットハッシュの取得を行う."""
    command = [ "git", "rev-parse", "HEAD", ]
    code, stdout, stderr =  start_process_return_string(command)
    edit_stdout = stdout.replace("\n", "")
    return edit_stdout


def del_binder_dir() -> None:
    """前後処理 開始前後にバインダーディレクトリを削除する."""
    binder_create_dir = f"{binder_base_dir}/{binder_user}_owner"

    if os.path.exists(binder_create_dir):
        os.chdir(binder_create_dir)
        try:
            for root, dirs, files in os.walk(binder_create_dir):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), stat.S_IRWXU)
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IRWXU)
            shutil.rmtree(binder_create_dir)
            os.chdir(home_dir)
        except Exception as e:
            pass
    os.chdir(home_dir)


def check_process(proc_name: str) -> bool:
    """プロセスのチェックを行う."""
    return ex_service.is_process(proc_name)


def get_rts_status(adress:str, ws:str, package_name:str) -> Any:
    """rtsのstatusを取得する."""
    return requests.get(f"{adress}/{ws}/packages/{package_name}/rts/status", headers=headers)


def chk_rtc(json_data: Any) -> Tuple[bool, bool, bool, bool]:
    """インストールされているRTCをチェックする."""
    is_testin_cpp = False
    is_Testout_cpp = False
    is_testin_py = False
    is_Testout_py = False
    for rtc in json_data['rtcs']:
        if rtc_test_in_cpp in rtc:
            is_testin_cpp = True
        if rtc_test_out_cpp in rtc:
            is_Testout_cpp = True
        if rtc_test_in_py in rtc:
            is_testin_py = True
        if rtc_test_out_py in rtc:
            is_Testout_py = True

    return (is_testin_cpp, is_Testout_cpp, is_testin_py, is_Testout_py)


def chk_status(response_data: Any, status: str, rtc_name:str) -> bool:
    """rtsのstatusをチェックする."""
    is_status = False
    for rtc in response_data['successful_RTCs']:
        if rtc_name in rtc and status in rtc:
            is_status = True

    return is_status


def chk_connect(response_data: Any, rtc_name: str) -> bool:
    """接続状態をチェックする."""
    is_connect = False
    for rtc in response_data['successful_RTCs']:
        if rtc_name in rtc and "Connected to" in rtc:
            is_connect = True
    return is_connect


def test06(setup_clean_package: Any) -> None:
    """試験ケース06 複数ホスト_複数RTCを利用するRTSの開発."""
    _test_06_01()
    _test_06_02()
    _test_06_03()
    _test_06_04()
    _test_06_05()
    _test_06_06()
    _test_06_07()
    _test_06_08()
    _test_06_09()


def _test_06_01() -> None:
    """試験ケース06-1 binderを作成する."""
    response = requests.post(f"{url}/binders/", data=json.dumps(binder_data), headers=headers)
    assert response.status_code == 200
    assert os.path.isdir(binder_dir)

    os.chdir(binder_dir)
    stdout = get_git_remote_info()
    assert binder_git in stdout
    os.chdir(home_dir)


def _test_06_02() -> None:
    """試験ケース06-2 binderに登録されているパッケージ一覧を取得する."""
    # No.1
    response = requests.get(f"{url}/binders/packages", headers=headers)
    assert response.status_code == 200
    assert len(list(response.json()["packages"])) > 0

    # No.2
    response = requests.get(f"{url}/binders/rtcs", headers=headers)
    assert response.status_code == 200
    assert len(list(response.json()["rtcs"])) > 0


def _test_06_03() -> None:
    """試験ケース06-3 DevelopWorkspaceでパッケージを開発する（新規作成）."""
    # No.1
    response = requests.post(f"{url}/{WS.dev}/packages", data=json.dumps(package_data), headers=headers)
    assert response.status_code == 200
    package_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2)
    assert os.path.isdir(package_dir)

    # No.2
    response = requests.get(f"{url}/{WS.dev}/packages", headers=headers)
    json_data = response.json()
    assert response.status_code == 200
    exist_package2 = False
    for item in json_data["packages"]:
        exist_package2 = package_name2 in str(item)
        if exist_package2:
            break
    assert exist_package2

    # No.3
    response = requests.get(f"{url}/{WS.dev}/packages/{package_name2}/rtcs", headers=headers)
    json_data = response.json()
    assert response.status_code == 200
    assert type(json_data["rtcs"]) is list
    assert json_data["rtcs"] == []

    # No.4
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rtcs/{rtc_test_in_cpp}/git/clone", headers=headers)
    assert response.status_code == 200
    rtc_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc" , rtc_test_in_cpp)
    assert os.path.isdir(rtc_dir)
    os.chdir(rtc_dir)
    assert rtc_test_in_cpp.lower() in get_git_remote_info()
    os.chdir(home_dir)

    # No.5
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rtcs/{rtc_test_out_cpp}/git/clone", headers=headers)
    assert response.status_code == 200
    rtc_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc" , rtc_test_out_cpp)
    assert os.path.isdir(rtc_dir)
    os.chdir(rtc_dir)
    assert rtc_test_out_cpp.lower() in get_git_remote_info()
    os.chdir(home_dir)

    # No.6
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rtcs/{rtc_test_in_py}/git/clone", headers=headers)
    assert response.status_code == 200
    rtc_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc" , rtc_test_in_py)
    assert os.path.isdir(rtc_dir)
    os.chdir(rtc_dir)
    assert rtc_test_in_py.lower() in get_git_remote_info()
    os.chdir(home_dir)

    # No.7
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rtcs/{rtc_test_out_py}/git/clone", headers=headers)
    assert response.status_code == 200
    rtc_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc" , rtc_test_out_py)
    assert os.path.isdir(rtc_dir)
    os.chdir(rtc_dir)
    assert rtc_test_out_py.lower() in get_git_remote_info()
    os.chdir(home_dir)

    # No.8
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/sync_rtc", headers=headers)
    assert response.status_code == 200
    sync_file_path = os.path.normpath(f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name2}/rtc/repository.yaml")
    with open(sync_file_path, "r") as yml:
        yml_data = yaml.safe_load(yml)
        rtc_list = list(yml_data.keys())
        assert rtc_test_in_cpp.lower() in rtc_list
        assert rtc_test_out_cpp.lower() in rtc_list
        assert rtc_test_in_py.lower() in rtc_list
        assert rtc_test_out_py.lower() in rtc_list

    # No.9
    execution_dir = os.path.dirname(__file__)
    origin_file = os.path.join(execution_dir, "DefaultSystem2.xml")
    distribute_file = os.path.join(execution_dir, "DefaultSystem_wk.xml")
    assert shutil.copyfile(origin_file, distribute_file)

    with open(distribute_file, encoding='utf-8') as f:
        lines = f.read()
    # 文字列置換
    lines = lines.replace("<IP address1>", ip)
    lines = lines.replace("<IP address2>", ip)
    with open(distribute_file, mode="w", encoding='utf-8') as f:
        f.write(lines)

    copy_file = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "system/DefaultSystem.xml")
    assert shutil.copyfile(distribute_file, copy_file)
    os.remove(distribute_file)

    # No.10
    ignore_file_path = os.path.normpath(f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name2}/.gitignore")
    with open(ignore_file_path, "w") as f:
        f.write("mgr.py")

    # No.11
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/git/init", headers=headers)
    assert response.status_code == 200
    init_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, ".git")
    assert os.path.exists(init_dir)

    # No.12
    response = requests.put(f"{url}/{WS.dev}/packages/{package_name2}/git/remote", data=json.dumps(git_data), headers=headers)
    assert response.status_code == 200
    remote_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2)
    os.chdir(remote_dir)
    assert git_url in get_git_remote_info()
    os.chdir(remote_dir)

    # No.13
    # masterブランチを削除、存在しない場合はエラーとなるため、1を許容する
    os.chdir(remote_dir)
    code, stdout, stderr = del_master_bransh()
    assert code == 0 or 1

    os.chdir(remote_dir)
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/git/commit", data=json.dumps(commit_data), headers=headers)
    assert response.status_code == 200
    os.chdir(package_dir)
    msg = get_git_log()
    assert "First Commit" in msg

    # No.14
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/git/push", headers=headers)
    assert response.status_code == 200

    os.chdir(remote_dir)
    stdout = git_pull()
    assert "Already up to date." in stdout
    os.chdir(remote_dir)


def _test_06_04() -> None:
    """試験ケース06-4 DevelopWorkspaceでパッケージをビルドする."""
    # No.1
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/build", headers=headers)
    assert response.status_code == 200
    # TestIn_cpp／TestOut_cpp
    bilud_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "bin")
    list = glob.glob(bilud_dir + "/*")
    chk_name1 = [s for s in list if rtc_test_in_cpp in s]
    assert len(chk_name1) > 0
    chk_name2 = [s for s in list if rtc_test_out_cpp in s]
    assert len(chk_name2) > 0
    # TestIn_py／TestOut_py
    bilud_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc", rtc_test_in_py)
    list = glob.glob(bilud_dir + "/*")
    chk_name3 = [s for s in list if rtc_test_in_py in s]
    assert len(chk_name3) > 0
    bilud_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "rtc", rtc_test_out_py)
    list = glob.glob(bilud_dir + "/*")
    chk_name4 = [s for s in list if rtc_test_out_py in s]
    assert len(chk_name4) > 0


def _test_06_05() -> None:
    """試験ケース06-5 DevelopWorkspaceでRTSを実行する."""
    # No.1
    response = requests.post(f"{url}/nameserver/start", headers=headers)

    # No.2
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rts/run", headers=headers)
    assert response.status_code == 200
    assert check_process("rtcd") or check_process("/usr/bin/rtcd_python3")

    # No.3
    response = get_rts_status(url, WS.dev, package_name2)
    assert response.status_code == 200
    # TestIn_cpp
    is_status_in = chk_status(response.json(), "Active", rtc_test_in_cpp)
    assert is_status_in
    is_connect_in = chk_connect(response.json(), rtc_test_in_cpp)
    assert is_connect_in
    # TestOut_cpp
    is_status_out = chk_status(response.json(), "Active", rtc_test_out_cpp)
    assert is_status_out
    is_connect_out = chk_connect(response.json(), rtc_test_out_cpp)
    assert is_connect_out
    # TestIn_py
    is_status_in = chk_status(response.json(), "Active", rtc_test_in_py)
    assert is_status_in
    is_connect_in = chk_connect(response.json(), rtc_test_in_py)
    assert is_connect_in
    # TestOut_py
    is_status_in = chk_status(response.json(), "Active", rtc_test_out_py)
    assert is_status_in
    is_connect_in = chk_connect(response.json(), rtc_test_out_py)
    assert is_connect_in

    # No.4
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/rts/terminate", headers=headers)
    assert response.status_code == 200
    assert not check_process("rtcd")
    assert not check_process("/usr/bin/rtcd_python3")

    # No.5
    response = requests.get(f"{url}/{WS.dev}/packages/{package_name2}/rts/logs", headers=headers)
    assert response.status_code == 200
    contentDisposition = response.headers['Content-Disposition']
    ATTRIBUTE = 'filename='
    file_name = contentDisposition[contentDisposition.find(ATTRIBUTE) + len(ATTRIBUTE):]

    save_file_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{file_name}"
    save_file_dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/test_log"

    os.chdir(DEVELOP_WORKSPACE_BASE_PATH)
    with open(save_file_path, 'wb') as save_file:
        save_file.write(response.content)
    with zipfile.ZipFile(file_name) as zf:
        os.mkdir(save_file_dir_path)
        os.chdir(save_file_dir_path)
        zf.extractall()
    assert set(os.listdir(save_file_dir_path)) == set(os.listdir(f"{DEVELOP_WORKSPACE_BASE_PATH}/{package_name2}/log"))

    # 後処理
    os.chdir(home_dir)
    os.remove(save_file_path)
    shutil.rmtree(save_file_dir_path)

    # No.6
    response = requests.post(f"{url}/nameserver/stop", headers=headers)


def _test_06_06() -> None:
    """試験ケース06-6 複数ホスト用にRTSProfileを変更する."""
    # No.1-1
    # 編集用にファイルをコピーする
    execution_dir = os.path.dirname(__file__)
    origin_file = os.path.join(execution_dir, "DefaultSystem2.xml")
    distribute_file = os.path.join(execution_dir, "DefaultSystem_wk.xml")
    assert shutil.copyfile(origin_file, distribute_file)

    with open(distribute_file, encoding='utf-8') as f:
        lines = f.read()

    # 文字列置換
    lines = lines.replace("<IP address1>", ip)
    lines = lines.replace("<IP address2>", ip2)

    with open(distribute_file, mode="w", encoding='utf-8') as f:
        f.write(lines)

    # No.1-2
    # 編集したファイルの再配布し、後始末
    copy_file = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2, "system/DefaultSystem.xml")
    assert shutil.copyfile(distribute_file, copy_file)
    os.remove(distribute_file)

    # No.2
    commit_data = {"comment": comment2}
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/git/commit", data=json.dumps(commit_data), headers=headers)
    assert response.status_code == 200
    package_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2)
    os.chdir(package_dir)
    msg = get_git_log()
    assert comment2 in msg
    os.chdir(home_dir)

    # No.3
    response = requests.post(f"{url}/{WS.dev}/packages/{package_name2}/git/push", headers=headers)
    assert response.status_code == 200

def _test_06_07() -> None:
    """試験ケース06-7 ExecuteWorkspaceにdeployする(複数ホスト)."""
    # No.1-1 コミットハッシュを取得する
    package_dir = os.path.join(DEVELOP_WORKSPACE_BASE_PATH, package_name2)
    os.chdir(package_dir)
    hash = git_commit_hash()
    assert len(hash) > 0
    os.chdir(home_dir)

    # No.1-2
    deploy_data = {"rts_git_url": git_url, "commit_hash": hash}
    response = requests.post(f"{url}/deploy/{WS.exec}/packages/deploy", data=json.dumps(deploy_data), headers=headers)
    assert response.status_code == 200

    # No.1-3
    package_dir = os.path.join(EXECUTE_WORKSPACE_BASE_PATH, exec_package_name)
    os.chdir(package_dir)
    chk_hash = git_commit_hash()
    os.chdir(home_dir)
    assert chk_hash == hash

    # No.1-4 TestIn_cpp/TestIn_py
    response = requests.get(f"{url}/{WS.exec}/packages/{exec_package_name}/rtcs", headers=headers)
    assert response.status_code == 200
    is_testin_cpp, is_testout_cpp, is_testin_py, is_testout_py = chk_rtc(response.json())
    assert is_testin_cpp
    assert not is_testout_cpp
    assert is_testin_py
    assert not is_testout_py

    # No.2-1
    deploy_data = {"rts_git_url": git_url, "commit_hash": hash}
    response = requests.post(f"{url2}/deploy/{WS.exec}/packages/deploy", data=json.dumps(deploy_data), headers=headers)
    assert response.status_code == 200

    # No.2-2 TestIn_cpp/TestIn_py
    response = requests.get(f"{url2}/{WS.exec}/packages/{exec_package_name}/rtcs", headers=headers)
    assert response.status_code == 200
    is_testin_cpp, is_testout_cpp, is_testin_py, is_testout_py = chk_rtc(response.json())
    assert not is_testin_cpp
    assert is_testout_cpp
    assert not is_testin_py
    assert is_testout_py


def _test_06_08() -> None:
    """試験ケース06-8 ExecuteWorkspaceでパッケージをビルドする(複数ホスト)."""
    # No.1-1 ローカル
    response = requests.post(f"{url}/{WS.exec}/packages/{exec_package_name}/build", headers=headers)
    assert response.status_code == 200
    # TestIn_cpp
    bilud_dir = os.path.join(EXECUTE_WORKSPACE_BASE_PATH, exec_package_name, "bin")
    list = glob.glob(bilud_dir + "/*")
    chk_name1 = [s for s in list if rtc_test_in_cpp in s]
    assert len(chk_name1) > 0
    # TestIn_py
    bilud_dir = os.path.join(EXECUTE_WORKSPACE_BASE_PATH, exec_package_name, "rtc", rtc_test_in_py)
    list = glob.glob(bilud_dir + "/*")
    chk_name2 = [s for s in list if rtc_test_in_py in s]
    assert len(chk_name2) > 0

    # No.2-1 リモート(レスポンスコードのチェックのみ)
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/build", headers=headers)
    assert response.status_code == 200

def _test_06_09() -> None:
    """試験ケース06-9 ExecuteWorkspaceでRTSを実行する(複数ホスト)."""
    response = requests.post(f"{url}/nameserver/start", headers=headers)
    response = requests.post(f"{url2}/nameserver/start", headers=headers)

    # No.3
    response = requests.post(f"{url}/{WS.exec}/packages/{exec_package_name}/rts/start", headers=headers)
    assert response.status_code == 200

    # No.4 IP Adress1 status(Inactive) TestIn_cpp/TestIn_py disconnect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert not is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_py)
    assert not is_connect

    # No.5 IP Adress2 start
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/start", headers=headers)
    assert response.status_code == 200

    # No.6 IP Adress2 status(Inactive) TestOut_cpp/TestOut_py disconnect
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_cpp)
    assert not is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert not is_connect

    # No.7 IP Adress2
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/connect", headers=headers)
    assert response.status_code == 200

    # No.8 IP Adress1 status(Inactive) TestIn_cpp/TestIn_py connect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_py)
    assert is_connect

    # No.9 IP Adress2 status(Inactive) TestOut_cpp/TestOut_py connect
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert is_connect

    # No.10 IP Adress2 activate
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/activate", headers=headers)
    assert response.status_code == 200

    # No.11 IP Adress1 status(Active) TestIn_cpp/TestIn_py connect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Active", rtc_test_in_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Active", rtc_test_in_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_py)
    assert is_connect

    # No.12 IP Adress2 status(Active) TestOut_cpp/TestOut_py connect
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Active", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Active", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert is_connect

    # No.13 IP Adress2 deactivate
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/deactivate", headers=headers)
    assert response.status_code == 200

    # No.14 IP Adress1 status(Inactive) TestIn_cpp/TestIn_py connect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_py)
    assert is_connect

    # No.15 IP Adress2 status(Inactive) TestOut_cpp/TestOut_py connect
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_cpp)
    assert is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert is_connect

    # No.16 IP Adress2 disconnect
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/disconnect", headers=headers)
    assert response.status_code == 200

    # No.17 IP Adress1 status(Inactive) TestIn_cpp/TestIn_py disconnect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert not is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_in_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_py)
    assert not is_connect

    # No.18 IP Adress2 status(Inactive) TestOut_cpp/TestOut_py disconnect
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_in_cpp)
    assert not is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert not is_connect

    # No.19 IP Adress1 terminate
    response = requests.post(f"{url}/{WS.exec}/packages/{exec_package_name}/rts/terminate", headers=headers)
    assert response.status_code == 200

    # No.20 IP Adress1 status(Inactive) TestOut_cpp/TestOut_py disconnect
    response = get_rts_status(url, WS.exec, exec_package_name)
    assert response.status_code == 200
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_cpp)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_cpp)
    assert not is_connect
    is_status = chk_status(response.json(), "Inactive", rtc_test_out_py)
    assert is_status
    is_connect = chk_connect(response.json(), rtc_test_out_py)
    assert not is_connect

    # No.21 IP Adress2 terminate
    response = requests.post(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/terminate", headers=headers)
    assert response.status_code == 200

    # No.22 IP Adress2 status
    response = get_rts_status(url2, WS.exec, exec_package_name)
    assert response.status_code == 200
    assert response.json() == {"failure_RTCs": [], "successful_RTCs": []}

    # No.23 IP Adress1 log
    response = requests.get(f"{url}/{WS.exec}/packages/{exec_package_name}/rts/logs", headers=headers)
    assert response.status_code == 200
    contentDisposition = response.headers['Content-Disposition']
    ATTRIBUTE = 'filename='
    file_name = contentDisposition[contentDisposition.find(ATTRIBUTE) + len(ATTRIBUTE):]

    save_file_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{file_name}"
    save_file_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/test_log"

    os.chdir(EXECUTE_WORKSPACE_BASE_PATH)
    with open(save_file_path, 'wb') as save_file:
        save_file.write(response.content)
    with zipfile.ZipFile(file_name) as zf:
        os.mkdir(save_file_dir_path)
        os.chdir(save_file_dir_path)
        zf.extractall()
    assert set(os.listdir(save_file_dir_path)) == set(os.listdir(f"{EXECUTE_WORKSPACE_BASE_PATH}/{exec_package_name}/log"))

    # 後処理
    os.chdir(home_dir)
    os.remove(save_file_path)
    shutil.rmtree(save_file_dir_path)

    # No.24 IP Adress2 log
    response = requests.get(f"{url2}/{WS.exec}/packages/{exec_package_name}/rts/logs", headers=headers)
    assert response.status_code == 200
    contentDisposition = response.headers['Content-Disposition']
    ATTRIBUTE = 'filename='
    file_name = contentDisposition[contentDisposition.find(ATTRIBUTE) + len(ATTRIBUTE):]
    assert file_name.endswith(".zip")

    save_file_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{file_name}"
    save_file_dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/test_log"

    os.chdir(EXECUTE_WORKSPACE_BASE_PATH)
    with open(save_file_path, 'wb') as save_file:
        save_file.write(response.content)
    with zipfile.ZipFile(file_name) as zf:
        os.mkdir(save_file_dir_path)
        os.chdir(save_file_dir_path)
        zf.extractall()
    assert len(os.listdir(save_file_dir_path)) > 0

    # 後処理
    os.chdir(home_dir)
    os.remove(save_file_path)
    shutil.rmtree(save_file_dir_path)

    response = requests.post(f"{url}/nameserver/stop", headers=headers)
    response = requests.post(f"{url2}/nameserver/stop", headers=headers)

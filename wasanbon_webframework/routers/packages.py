"""RTCの実行・停止に関するモジュール."""
import logging
from typing import Any, Dict

import yaml
from fastapi import APIRouter, Depends, HTTPException, status

import wasanbon_webframework.services.packages_service as service

from ..models.commit import Commit
from ..models.packagename import PackageName
from ..models.rtcname import RtcName
from ..models.url import URL
from ..models.ws import WS

import subprocess

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["packages"], dependencies=[])


@router.get(
    "/{ws}/test",
    description="""
        List Packages installed in specified workspace.
        $ wasanbon-admin.py package list

        """,
)
def ttest(ws: WS) -> Dict[str, Any]:
    """指定のワークスペースのパッケージ一覧を取得する.

    $ wasanbon-admin.py package list -l を指定のワークスペース配下のものでフィルタ

    Args:
        ws(str): ワークスペース種別

    Returns:
        Dict: 実行結果
    """
    result = subprocess.run(
        ["ls", "/home/rsdlab/"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True  # Python 3.8 ではこれで text=True と同じ
    )
    
    if result.returncode == 0:
        return result.stdout  # 正常時は標準出力を返す
    else:
        return f"Error: {result.stderr}" 
     # output_lines = []  # 出力をためておくリスト

    # try:
    #     process = subprocess.Popen(
    #         ["roscore"],
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT,
    #         universal_newlines=True
    #     )

    #     for line in process.stdout:
    #         line = line.strip()
    #         print(line)               # リアルタイム表示
    #         output_lines.append(line)  # リストに追加

    # except KeyboardInterrupt:
    #     print("終了します...")
    #     process.terminate()

    # return output_lines

    # result = subprocess.run(
    #     ["ls", "/home/rsdlab/"],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     universal_newlines=True  # Python 3.8 ではこれで text=True と同じ
    # )
    
    # if result.returncode == 0:
    #     return result.stdout  # 正常時は標準出力を返す
    # else:
    #     return f"Error: {result.stderr}"

@router.get(
    "/{ws}/packages",
    description="""
        List Packages installed in specified workspace.
        $ wasanbon-admin.py package list

        """,
)  
def get_packages(ws: WS) -> Dict[str, Any]:
    """指定のワークスペースのパッケージ一覧を取得する.

    $ wasanbon-admin.py package list -l を指定のワークスペース配下のものでフィルタ

    Args:
        ws(str): ワークスペース種別

    Returns:
        Dict: 実行結果
    """
    code, yaml_data, stderr = service.get_packages_list(ws)
    if code == 0 and yaml_data is not None:
        print("yahho")
        # return {"debug": "yahho", "packages": [{k: yaml_data[k]} for k in yaml_data]}
        return {"packages": [{k: yaml_data[k]} for k in yaml_data]}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": yaml_data, "stderr": stderr}
        )


@router.post(
    "/{ws}/packages",
    description="""
        Create Package
        $ wasanbon-admin.py package create <PACK_NAME>

        """,
)
def create_new_package(ws: WS, packages: PackageName) -> Dict[str, Any]:
    """DWに新規パッケージ一覧を作成する.

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.create_packages(ws, packages.name)
    if code == 0:
        return {"message": [yaml.safe_load(stdout)]}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.delete(
    "/{ws}/packages/{name}",
    description="""
        Delete Package
        $ wasanbon-admin.py package delete -r <PACK_NAME>

        """,
)
def delete_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """DWのパッケージを削除する.

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.delete_packages(name.name)
    if code == 0:
        return {"message": f"Removing package {name.name}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.delete(
    "/{ws}/packages/{name}/rtcs/{rtc_name}",
    description="""
        Delete RTC from Package
        $ ./mgr.py rtc delete <RTC_NAME>

        """,
)
def delete_rtc_in_package(
    ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Delete RTC from Package.

    $ ./mgr.py rtc delete <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )
    code, stdout, stderr = service.delete_rtc_package(ws, name.name, rtc_name.rtc_name)
    # -vオプションでもスタックトレースが取得できないため、メッセージを生成して返却する
    if code == 0:
        return {"message": f"Deleting RTC ({rtc_name.rtc_name}) from Package ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execute Failured Delete RTC ({rtc_name.rtc_name}) from Package ({name.name})",
        )


@router.post(
    "/{ws}/packages/{name}/git/clone",
    description="""
        Cloning Package from repository.
        $ wasanbon-admin.py repository clone <PACKAGE_REPOSITORY_NAME>

        """,
)
def clone_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Cloning Package from repository.

    $ wasanbon-admin.py repository clone <PACKAGE_REPOSITORY_NAME>

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_clone_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    # 既にcloneされている場合　code = 4294967295
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/git/init",
    description="""
        Create local repository
        ./mgr.py admin git_init

        """,
)
def git_init_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Create local repository.

    ./mgr.py admin git_init

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_init_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.post(
    "/{ws}/packages/{name}/git/commit",
    description="""
        Commit changes to local Package repository
        ./mgr.py admin commit <COMMENT>

        """,
)
def git_commit_package(ws: WS, comment: Commit, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Commit changes to local Package repository.

    ./mgr.py admin commit <COMMENT>

    Args:
        ws(WS): ワークスペース種別
        commit(Commit): コメント
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_commit_service(ws, comment.comment, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/git/push",
    description="""
        Commit changes to local Package repository
        ./mgr.py admin push

        """,
)
def git_push_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Push Repository to server (default origin, master).

    ./mgr.py admin push

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_push_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/sync_rtc",
    description="""
        Synchronize rtc/repository.yaml file and each rtc repository version hash.
        ./mgr.py repository sync

        """,
)
def sync_rtcs_in_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Synchronize rtc/repository.yaml file and each rtc repository version hash.

    ./mgr.py repository sync

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_sync_rtc_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.put(
    "/{ws}/packages/{name}/git/remote",
    description="""
        Add git remote.
        git remote add origin <URL>

        """,
)
def git_add_remote_to_package(ws: WS, url: URL, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Add git remote.

    git remote add origin <URL>

    Args:
        ws(str): ワークスペース種別
        url(URL): URL
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_add_remote_service(ws, url.url, name.name)
    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.get(
    "/{ws}/packages/{name}/git/status",
    description="""
        Show status of package local repository.
        ./mgr admin status

        """,
)
def get_git_status_of_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Show status of package local repository.

    ./mgr admin status

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.git_status_service(ws, name.name)

    if code == 0:
        return {"status": yaml.safe_load(stdout)}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.get(
    "/{ws}/packages/{name}/rtcs",
    description="""
        List RTC in current Package.
        $ ./mgr.py rtc list

        """,
)
def get_rtcs_in_package(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, Any]:
    """List RTC in current Package.

    $ ./mgr.py rtcs list

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名
    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.get_rtcs_list(ws, name.name)
    if code == 0 and stdout is not None:
        return {"rtcs": [{k: stdout[k]} for k in stdout]}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/git/clone",
    description="""
        Clone RTC to package.
        $ ./mgr.py repository clone <REPO_NAME>

        """,
)
def clone_rtc_in_package(
    ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Clone RTC to package.

        $ ./mgr.py repository clone <REPO_NAME>

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_clone_rtc_service(ws, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/git/init",
    description="""
        Initialize git repository in RTC directory.
        $ ./mgr.py repository git_init <RTC_NAME>

        """,
)
def git_init_rtc(
    ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Initialize git repository in RTC directory.

    $ ./mgr.py repository git_init <RTC_NAME>

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_init_rtc_service(ws, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/git/commit",
    description="""
        Commit local changes to local repository.
        $ ./mgr.py repository commit <RTC_NAME> <COMMENT>

        """,
)
def git_commit_rtc(
    ws: WS, comment: Commit, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Commit local changes to local repository.

    $ ./mgr.py repository commit <RTC_NAME> <COMMENT>

    Args:
        ws(WS): ワークスペース種別
        commit(Commit): コメント
        name(PackageName): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_commit_rtc_service(ws, comment.comment, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/git/push",
    description="""
        Push Repository to server (default origin, master)
        $ ./mgr.py repository push <RTC_NAME>

        """,
)
def git_push_rtc(
    ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Push Repository to server (default origin, master).

    $ ./mgr.py repository push <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_push_rtc_service(ws, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.put(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/git/remote",
    description="""
        Add git remote.
        git remote add origin <URL>

        """,
)
def git_add_remote_to_rtc(
    ws: WS, url: URL, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)
) -> Dict[str, str]:
    """Add git remote.

    git remote add origin <URL>

    Args:
        ws(str): ワークスペース種別
        url(URL): URL
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    if not service.is_write_workspace(ws):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Execute workspace is forbidden to write directly"
        )

    code, stdout, stderr = service.git_add_remote_rtc_service(ws, url.url, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.get(
    "/{ws}/packages/{name}/rtcs/git/status",
    description="""
        Show Repository Status of RTCs.
        $ ./mgr.py repository status

        """,
)
def get_git_status_of_all_rtcs(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Show Repository Status of RTCs.

    $ ./mgr.py repository status

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.git_rtc_status_service(ws, name.name)

    if code == 0:
        return {"status": yaml.safe_load(stdout)}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )

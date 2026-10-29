"""binderに関するモジュール."""
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

import wasanbon_webframework.services.binder_service as service
from wasanbon_webframework.models.packagenameforbinder import PackageNameForBinder
from wasanbon_webframework.models.rtcname import RtcName
from wasanbon_webframework.models.rtcnameforbinder import RtcNameForBinder
from wasanbon_webframework.models.ws import WS

from ..models.bindername import BinderName
from ..models.binderuser import BinderUser
from ..models.commit import Commit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/binders", tags=["binders"], dependencies=[])


@router.get(
    "/",
    description="""
        List Installed Binders.
        $ wasanbon-admin.py binder list

        """,
)
def get_binder() -> Dict[str, Any]:
    """List Installed Binders.

    $ wasanbon-admin.py binder list

    Returns:
        Dict: 実行結果

    """
    code, yaml_data, stderr = service.get_binder_list()
    if code == 0 and yaml_data is not None:
        return {"binders": [{key: yaml_data[key]} for key in yaml_data]}
    else:
        raise HTTPException(status_code=500, detail={"stdout": yaml_data, "stderr": stderr})


@router.post(
    "/update",
    description="""
        Update Binder. Download Binder from repository.
        $ wasanbon-admin.py binder update -v

        """,
)
def update_binder() -> Dict[str, str]:
    """Update Binder. Download Binder from repository.

    $ wasanbon-admin.py binder update -v

    Returns:
        Dict: 実行結果

    """
    code, stdout, stderr = service.binder_update_service()

    if code == 0:
        return {"message": stdout}

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.get(
    "/packages",
    description="""
        List Package repositories in your binders.
        $ wasanbon-admin.py binder packages -l

        """,
)
def get_packages_in_binders() -> Dict[str, Any]:
    """List Package repositories in your binders.

    $ wasanbon-admin.py binder packages -l

    Returns:
        Dict: 実行結果
    """
    code, yaml_data, stderr = service.get_binder_packages()
    if code == 0 and yaml_data is not None:
        return {"packages": [{key: yaml_data[key]} for key in yaml_data]}
    else:
        raise HTTPException(status_code=500, detail={"stdout": yaml_data, "stderr": stderr})


@router.get(
    "/rtcs",
    description="""
        Show RTC Repositories in your binders.
        $ wasanbon-admin.py binder rtcs -l

        """,
)
def get_rtcs_in_binders() -> Dict[str, Any]:
    """Show RTC Repositories in your binders.

    $ wasanbon-admin.py binder rtcs -l

    Returns:
        Dict: 実行結果
    """
    code, yaml_data, stderr = service.get_binder_rtcs()
    if code == 0 and yaml_data is not None:
        return {"rtcs": [{key: yaml_data[key]} for key in yaml_data]}
    else:
        raise HTTPException(status_code=500, detail={"stdout": yaml_data, "stderr": stderr})


@router.post(
    "/",
    description="""
        Create Binder on Git-hosting-services.
        $ wasanbon-admin.py binder create -v -u <USER> -p <PASSWORD> -t <TOKEN>

        """,
)
def create_binder(binderuser: BinderUser) -> Dict[str, str]:
    """Create Binder on Git-hosting-services.

    $ wasanbon-admin.py binder create -v -u <USER> -p <PASSWORD> -t <TOKEN>

    Args:
        binderuser(BinderUser): ユーザ名、トークン

    Returns:
        Dict: 実行結果
    """
    temp_pw = "temp_pw"
    code, stdout, stderr = service.binder_create_service(binderuser.username, temp_pw, binderuser.token)
    logger.info(stdout)
    if code == 0 or code == 1:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{binder_name}/commit",
    description="""
        Commit changes of binder file (.yaml) to local repository.
        $ wasanbon-admin.py binder commit <BINDER_OWNER_NAME> <COMMENT>

        """,
)
def commit_binder(comment: Commit, binder_name: BinderName = Depends(BinderName)) -> Dict[str, str]:
    """Commit changes of binder file (.yaml) to local repository.

    $ wasanbon-admin.py binder commit <BINDER_OWNER_NAME> <COMMENT>

    Args:
        comment(str): コミットメッセージ
        binder_name(BinderName): binder名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.binder_commit_service(binder_name.binder_name, comment.comment)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{binder_name}/push",
    description="""
        Commit changes of binder file (.yaml) to local repository.
        This command is currently not supported, so it returns 500. if you want to push, access the site via ssh and execute the command.

        $ wasanbon-admin.py binder commit -p <BINDER_OWNER_NAME> <COMMENT>

        """,
)
def push_binder(comment: Commit, binder_name: BinderName = Depends(BinderName)) -> Dict[str, str]:
    """Commit changes of binder file (.yaml) to local repository.

    $ wasanbon-admin.py binder commit -p <BINDER_OWNER_NAME> <COMMENT>

    Args:
        comment(Commit): コミットメッセージ
        binder_name(BinderName): binder名

    Returns:
        Dict: 実行結果
    """
    stderr = f"Binder push API is unavailable on this version due to change of GitHub's authentication  method.{os.linesep}Support for password authentication was removed on August 13, 2021.{os.linesep}Please see https://docs.github.com/en/get-started/getting-started-with-git/about-remote-repositories#cloning-with-https-urls for information on currently recommended modes of authentication."
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"stdout": "", "stderr": stderr},
    )


@router.post(
    "/{binder_name}/packages",
    description="""
        Add This package information to binder
        $ ./mgr.py binder add_package <BINDER_NAME>

        """,
)
def add_package_to_binder(
    package_name: PackageNameForBinder, binder_name: BinderName = Depends(BinderName)
) -> Dict[str, str]:
    """Add This package information to binder.

    $ ./mgr.py binder add_package <BINDER_NAME>

    Args:
        package_name(PackageNameForBinder): package名
        binder_name(BinderName): binder名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.binder_add_package_service(
        package_name.ws, binder_name.binder_name, package_name.package_name
    )

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{binder_name}/rtcs",
    description="""
        Add RTC information to binder
        $ ./mgr.py binder add_rtc <BINDER_NAME> <RTC_NAME>

        """,
)
def add_rtc_to_binder(rtc_name: RtcNameForBinder, binder_name: BinderName = Depends(BinderName)) -> Dict[str, str]:
    """Add RTC information to binder.

    $ ./mgr.py binder add_rtc <BINDER_NAME> <RTC_NAME>

    Args:
        rtc_name(RtcNameForBinder): RTC名
        binder_name(BinderName): binder名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.binder_add_rtc_service(
        rtc_name.ws, binder_name.binder_name, rtc_name.package_name, rtc_name.rtc_name
    )

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.put(
    "/{binder_name}/package/{ws}/{package_name}",
    description="""
        Update this package information to binder
        $ ./mgr.py binder update_package <BINDER_NAME>

        """,
)
def update_package_in_binder(
    ws: WS,
    binder_name: BinderName = Depends(BinderName),
    package_name: PackageNameForBinder = Depends(PackageNameForBinder),
) -> Dict[str, str]:
    """Update this package information to binder.

    $ ./mgr.py binder update_package <BINDER_NAME>

    Args:
        ws(WS): ワークスペース種別
        binder_name(BinderName): binder名
        package_name(PackageNameForBinder): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.update_package_in_binder_service(
        ws, binder_name.binder_name, package_name.package_name
    )

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )


@router.put(
    "/{binder_name}/rtc/{ws}/{package_name}/{rtc_name}",
    description="""
        Update RTC information to binder
        $ ./mgr.py binder update_rtc <BINDER_NAME> <RTC_NAME>

        """,
)
def update_rtc_in_binder(
    ws: WS,
    binder_name: BinderName = Depends(BinderName),
    package_name: PackageNameForBinder = Depends(PackageNameForBinder),
    rtc_name: RtcName = Depends(RtcName),
) -> Dict[str, str]:
    """Update RTC package information to binder.

    $ ./mgr.py binder update_rtc <BINDER_NAME> <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        binder_name(BinderName): binder名
        package_name(PackageNameForBinder): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.update_rtc_in_binder_service(
        ws, binder_name.binder_name, package_name.package_name, rtc_name.rtc_name
    )

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"stdout": stdout, "stderr": stderr}
        )

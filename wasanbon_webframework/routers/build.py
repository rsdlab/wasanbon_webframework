"""ビルドに関するモジュール."""
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

import wasanbon_webframework.services.build_service as service

from ..models.packagename import PackageName
from ..models.rtcname import RtcName
from ..models.ws import WS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["build"], dependencies=[])


@router.post(
    "/{ws}/packages/{name}/build",
    description="""
        Build RTC in current Package.
        $ ./mgr.py rtc build all

        """,
)
def build_all_rtcs(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Build RTC in current Package.

    $ ./mgr.py rtc build all

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.build_all_rtcs_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )
    


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/build",
    description="""
        Build RTC in current Package.
        $ ./mgr.py rtc build <RTC_NAME>

        """,
)
def build_rtc(ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)) -> Dict[str, str]:
    """Build RTC in current Package.

    $ ./mgr.py rtc build <RTC_NAME>

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.build_rtc_service(ws, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/clean",
    description="""
        Clean RTC in current Package.
        $ ./mgr.py rtc clean all

        """,
)
def clean_all_rtcs(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Clean RTC in current Package.

    $ ./mgr.py rtc clean all

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.clean_all_rtcs_service(ws, name.name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rtcs/{rtc_name}/clean",
    description="""
        Clean RTC in current Package.
        $ ./mgr.py rtc clean <RTC_NAME>

        """,
)
def clean_rtc(ws: WS, name: PackageName = Depends(PackageName), rtc_name: RtcName = Depends(RtcName)) -> Dict[str, str]:
    """Clean RTC in current Package.

    $ ./mgr.py rtc clean <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.clean_rtc_service(ws, name.name, rtc_name.rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

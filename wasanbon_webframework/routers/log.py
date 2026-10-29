"""ログに関するモジュール."""
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

import wasanbon_webframework.services.log_service as service

from ..models.packagename import PackageName
from ..models.ws import WS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["log"], dependencies=[])


@router.get(
    "/{ws}/packages/{name}/rts/logs",
    description="""
        Get zip of log files of each RTC in package.

        """,
)
def get_logs_by_rtc(ws: WS, name: PackageName = Depends(PackageName)) -> StreamingResponse:
    """RTCごとにログファイルをzipでまとめて取得する.

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        StreamingResponse: zipファイル
    """
    code, log_file_list = service.get_log_file_list(ws, name.name)

    if len(log_file_list) == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LogFile not found")
    elif code == 1:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=log_file_list[0])

    try:
        response = service.make_zipfile_as_streaming_response(ws, name.name, log_file_list)
    except Exception:
        stderr = traceback.format_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=stderr)

    return response

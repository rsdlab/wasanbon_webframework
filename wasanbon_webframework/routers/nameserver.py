"""ネームサーバーの起動。再起動・停止・ステータス確認のモジュール."""
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from ..services.nameserver_service import check_name_server, restart_name_server, start_name_server, stop_name_server
# No model dependencies required in this router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nameserver", tags=["nameserver"], dependencies=[])


@router.post(
    "/start",
    description="""
        Start nameserver of a host.

        $ wasanbon-admin.py nameserver start
        """,
)
def nameserver_start(port: str = "") -> Dict[str, str]:
    """ホストのnameserverを起動する.

    $ wasanbon-admin.py nameserver start

    Args:
        port(str): ポート番号

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = start_name_server(port)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/restart",
    description="""
        Restart nameserver of a host.

        $ wasanbon-admin.py nameserver restart
        """,
)
def nameserver_restart() -> Dict[str, str]:
    """ホストのnameserverを再起動する.

    $ wasanbon-admin.py nameserver restart

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = restart_name_server()

    if code == 0 or code == 1:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/stop",
    description="""
        Stop nameserver of a host.
        If a nameserver that has not been started via wasanbon-webframework is running, stop the nameserver beforehand because an error will occur.

        $ wasanbon-admin.py nameserver stop
        """,
)
def nameserver_stop() -> Dict[str, str]:
    """ホストのnameserverを終了する.

    $ wasanbon-admin.py nameserver stop

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = stop_name_server()

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.get(
    "/",
    description="""
        Check status of nameserver.

        $ wasanbon-admin.py nameserver check_running
        """,
)
def nameserver_check_running(port: str = "") -> Dict[str, str]:
    """ホストのnameserverの起動状態を確認する.

    $ wasanbon-admin.py nameserver check_running

    Args:
        port(str): ポート番号

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = check_name_server(port)

    if code == 0 or code == 1:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

 

"""RTCの実行・停止に関するモジュール."""
import logging
from typing import Any, Dict, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, status

import wasanbon_webframework.services.execution_service as service

from ..models.packagename import PackageName
from ..models.rtcname import RtcName
from ..models.ws import WS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["execution"], dependencies=[])


@router.post(
    "/{ws}/packages/{name}/module/run/{module_name}",
    description="""
        Launch a module in the system.
        $ ./mgr.py module run <MODULE_NAME> -b

        """,
)
def run_module(ws: WS, module_name: str, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    code, stdout, stderr = service.run_module(ws, name.name, module_name)

    if code == 0:
        return {"message": f"Module '{module_name}' Started in Package ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

@router.post(
    "/{ws}/packages/{name}/system/run/{system_name}",
    description="""
        Launch a module in the system.
        $ ./mgr.py system run <SYSTEM_NAME> -b

        """,
)
def run_system_ex(ws: WS, system_name: str, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    code, stdout, stderr = service.run_system_ex(ws, name.name, system_name)

    if code == 0:
        return {"message": f"System '{system_name}' Started in Package ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/run",
    description="""
        Launch System.
        $ ./mgr.py system run -v -b

        """,
)
def run_system(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Launch System.

    $ ./mgr.py system run -v -b

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.run_system(ws, name.name)

    if code == 0:
        return {"message": f"System Started ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/start",
    description="""
        Start system without activation (bellow command) or execute an RTC if spacified.
        $ ./mgr.py system run -f <system.xml> -p -b or ./mgr.py rtc run <RTC_NAME>

        """,
)
def start_system(
    ws: WS, rtc_name: Optional[RtcName] = None, name: PackageName = Depends(PackageName)
) -> Dict[str, str]:
    """Start system without activation (bellow command) or execute an RTC if spacified.

    $ ./mgr.py system run -f <system.xml> -p -b or ./mgr.py rtc run <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        rtc_name(RtcName): RTC名
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.start_system(ws, name.name, rtc_name)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/connect",
    description="""
        Connect RTC ports.

        rtresurrect system.xml -v
        """,
)
def rtresurrect_connections(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """RTCのポートを接続する.

    rtresurrect system.xml -v

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.rtresurrect_connections(ws, name.name)
    if code == 0:
        return {"rtresurrect": "RT System Connection Resurrected"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/disconnect",
    description="""
        Disconnect RTC ports.

        rtteardown system.xml -v
        """,
)
def disconnect_connections(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """RTCのポートを切断する.

    rtteardown system.xml -v

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.disconnect_connections(ws, name.name)
    if code == 0:
        return {"rtteardown": "RT System Removed Connection"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/activate/",
    description="""
        Activate RTCs.
        rtstart system.xml

        """,
)
def activate_rtcs(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Activate RTCs.

    rtstart system.xml -v

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果

    """
    code, stdout, stderr = service.activate_rtcs(ws, name.name)
    if code == 0:
        return {"message": f"RT System Started ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )


@router.post(
    "/{ws}/packages/{name}/rts/deactivate/",
    description="""
        Deactivate RTCs.
        rtstop system.xml

        """,
)
def deactivate_rtcs(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Deactivate RTCs.

    rtstop system.xml -v

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果

    """
    code, stdout, stderr = service.deactivate_rtcs(ws, name.name)
    if code == 0:
        return {"message": f"RT System Stoped ({name.name})"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

#RTM用
@router.get(
    "/{ws}/packages/{name}/rts/status",
    description="""
        Check status and port connections of all RTCs.
        rtcat -l <RTC_FULL_PATH>

        """,
)
def rtc_status(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, Any]:
    """RTCの死活状況、ポート接続状態を取得する.

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, out_list, err_list = service.rtc_status(ws, name.name)
    if code == 0:
        return {"successful_RTCs": out_list, "failure_RTCs": err_list}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": out_list, "stderr": err_list},
        )


@router.post(
    "/{ws}/packages/{name}/rts/terminate/",
    description="""
        Terminate Launched System(bellow command) or teminate an RTC if spacified.
        $ ./mgr.py system terminate

        """,
)
def terminate_system(
    ws: WS, rtc_name: Optional[RtcName] = None, name: PackageName = Depends(PackageName)
) -> Dict[str, str]:
    """Terminate Launched System(bellow command) or teminate an RTC if spacified.

    $ ./mgr.py system terminate -v

    Args:
        ws(str): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Dict: 実行結果
    """
    code, stdout, stderr = service.terminate_system(ws, name.name, rtc_name)
    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

# #ROS1用
# @router.put(
#     "/set/ros/{server_ip}",
#     description="""
#         ros setup in .bashrc
#         $ setup

#         """,
# )
# def set_ros(server_ip: str, request: Request) -> Dict[str, bool]:
#     """ROS_IPとROS_MASTER_URIを設定する.

#     Args:
#         server_ip (str): 確認するROSマスターのIPアドレス
#         request (Request): リクエスト情報

#     Returns:
#         Dict[str, bool]: {"is_ok": True/False}
#     """
#     is_ok = service.set_ros_network_settings(server_ip, request)
#     return {"is_ok": is_ok}

# @router.post(
#     "/roscore/run",
#     description="""
#         run roscore
#         $ roscore

#         """,
# )
# def roscore_run() -> Dict[str, str]:
#     code, stdout, stderr = service.roscore_run()

#     if code == 0:
#         return {"message": stdout}
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"stdout": stdout, "stderr": stderr},
#         )

#ROS2用
@router.put(
    "/set/ros2/{domain_id}",
    description="Set ROS_DOMAIN_ID",
)
def set_ros2(domain_id: int) -> Dict[str, bool]:
    is_ok = service.set_ros2_network_settings(domain_id)
    return {"is_ok": is_ok}

    
@router.get(
    "/{ws}/packages/{name}/check/middleware",
    description="""
        Run './mgr.py module middleware' in the specified package.
        """,
)
def middleware_check(ws: WS, name: PackageName = Depends(PackageName)) -> Dict[str, str]:
    """Run './mgr.py module middleware' and return its output."""
    code, stdout, stderr = service.middleware_check(ws, name.name)

    if code == 0:
        return stdout
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

# #ROS1用
# @router.get(
#     "/server/check/{server_ip}",
#     description="""
#         Check if ROS_IP and ROS_MASTER_URI are set correctly.

#         - Checks if `echo $ROS_IP` matches the request host.
#         - Checks if `echo $ROS_MASTER_URI` contains the `server_ip`.
#         """,
#     response_model=Dict[str, bool],
# )
# def check_server_config(server_ip: str, request: Request) -> Dict[str, bool]:
#     """ROS_IPとROS_MASTER_URIの設定を確認する.

#     Args:
#         server_ip (str): 確認するROSマスターのIPアドレス
#         request (Request): リクエスト情報

#     Returns:
#         Dict[str, bool]: {"is_ok": True/False}
#     """
#     is_ok = service.check_ros_network_settings(server_ip, request)
#     return {"is_ok": is_ok}

#ROS2用
@router.get(
    "/ros2/check/{domain_id}",
    description="Check ROS_DOMAIN_ID",
    response_model=Dict[str, bool],
)
def check_ros2(domain_id: int) -> Dict[str, bool]:
    is_ok = service.check_ros2_network_settings(domain_id)
    return {"is_ok": is_ok}


@router.put(
    "/{ws}/packages/{name}/server/set/{server_ip}/{domain_id}/{system_name}",
)
def set_network_config_plus_ros2(
    ws: WS,
    server_ip: str,
    domain_id: int,
    system_name: str,
    request: Request,
    name: PackageName = Depends(PackageName),
) -> Dict[str, str]:

    host_header = request.headers.get("host")
    client_ip = host_header.split(":", 1)[0] if host_header else None

    if not client_ip:
        client_ip = request.url.hostname
    if not client_ip:
        client_ip = request.client.host

    if not client_ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Could not determine local IP"},
        )

    code, stdout, stderr = service.set_server_plus_ros2(
        ws,
        name.name,
        server_ip,
        client_ip,
        domain_id,
        system_name,
    )

    if code == 0:
        return {"message": stdout}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"stdout": stdout, "stderr": stderr},
    )

@router.put(
    "/{ws}/packages/{name}/server/set/{server_ip}/{domain_id}",
)
def set_network_config_ros2(
    ws: WS,
    server_ip: str,
    domain_id: int,
    request: Request,
    name: PackageName = Depends(PackageName),
) -> Dict[str, str]:

    host_header = request.headers.get("host")
    client_ip = host_header.split(":", 1)[0] if host_header else None

    if not client_ip:
        client_ip = request.url.hostname
    if not client_ip:
        client_ip = request.client.host

    if not client_ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Could not determine local IP"},
        )

    code, stdout, stderr = service.set_server_ros2(
        ws,
        name.name,
        server_ip,
        client_ip,
        domain_id,
    )

    if code == 0:
        return {"message": stdout}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"stdout": stdout, "stderr": stderr},
    )

##旧バージョン
# @router.put(
#     "/{ws}/packages/{name}/server/set/{server_ip}/{system_name}",
#     description="""
#         Set network config.
#         $ ./mgr.py server set <SERVER_IP> <LOCAL_IP> <SYSTEM_FILE>

#         """,
# )
# def set_network_config_plus(
#     ws: WS,
#     server_ip: str,
#     system_name: str,
#     request: Request,
#     name: PackageName = Depends(PackageName),
# ) -> Dict[str, str]:
#     host_header = request.headers.get("host")
#     client_ip = host_header.split(":", 1)[0] if host_header else None
#     if not client_ip:
#         client_ip = request.url.hostname
#     if not client_ip:
#         client_ip = request.client.host
#     if not client_ip:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Could not determine server IP for ROS_IP"},
#         )
#     code, stdout, stderr = service.set_server_plus(ws, name.name, server_ip, client_ip, system_name)

#     if code == 0:
#         return {"message": stdout}
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"stdout": stdout, "stderr": stderr},
#         )

# @router.put(
#     "/{ws}/packages/{name}/server/set/{server_ip}",
#     description="""
#         Set network config.
#         $ ./mgr.py server set <SERVER_IP> <LOCAL_IP>

#         """,
# )
# def set_network_config(
#     ws: WS,
#     server_ip: str,
#     request: Request,
#     name: PackageName = Depends(PackageName),
# ) -> Dict[str, str]:
#     host_header = request.headers.get("host")
#     client_ip = host_header.split(":", 1)[0] if host_header else None
#     if not client_ip:
#         client_ip = request.url.hostname
#     if not client_ip:
#         client_ip = request.client.host
#     if not client_ip:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Could not determine server IP for ROS_IP"},
#         )
#     code, stdout, stderr = service.set_server(ws, name.name, server_ip, client_ip)

#     if code == 0:
#         return {"message": stdout}
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"stdout": stdout, "stderr": stderr},
#         )

"""Deployのサービスモジュール."""
import logging
import os
import traceback
import xml.etree.ElementTree as Et
from typing import List, Tuple

from wasanbon_webframework.config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH
from wasanbon_webframework.models.ws import WS

logger = logging.getLogger(__name__)


def get_basepath(ws: WS) -> str:
    """wsに対応するパスを返却する.

    Args:
        ws(str): ワークスペース名

    Returns:
        str:実行パス
    """
    # パスの返却
    if ws == WS.dev:
        return DEVELOP_WORKSPACE_BASE_PATH
    elif ws == WS.exec:
        return EXECUTE_WORKSPACE_BASE_PATH

    return ""


def get_rts_host(ws: WS, pkg_name: str) -> Tuple[List[str], List[str]]:
    """DefaultSystem.xmlからpathUriを取得する.

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        rts_host_list: pathUri一覧
    """
    exec_path = os.path.join(get_basepath(ws), pkg_name)
    xml_file = "system/DefaultSystem.xml"
    rts_host_list = []
    error_list = []
    try:
        xml_obj = Et.parse(os.path.join(exec_path, xml_file)).getroot()

        for child in xml_obj.findall("{http://www.openrtp.org/namespaces/rts}Components"):
            uri = child.get("{http://www.openrtp.org/namespaces/rts}pathUri")
            rts_host_list.append(str(uri))
    except FileNotFoundError:
        error_list = [traceback.format_exc()]
        logger.error(traceback.format_exc())

    return (rts_host_list, error_list)


def is_write_workspace(ws: WS) -> bool:
    """書き込みが許可されているワークスペースであるかチェックする.

    Args:
        ws(str): ワークスペース種別

    Returns:
        bool: 判定結果
    """
    if ws.value == WS.dev:
        return True
    else:
        return False

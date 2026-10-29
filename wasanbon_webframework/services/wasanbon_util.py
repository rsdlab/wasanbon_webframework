"""wasanbonコマンドモジュール."""
import sys
from typing import List


def _generate_wasanbon_admin_command(*args: List[str]) -> List[str]:
    """wasanbon-admin.py系のコマンドを生成する.

    Args:
        args(List[str]): wasanbon-admin.py 以降のコマンド

    Returns:
        List[str]: 実行結果
    """
    # リストを用意する
    ret = ["wasanbon-admin.py"]
    # リストの末尾に、*argsのリストを加える
    ret.extend(*args)
    return ret


def _generate_mgr_command(path: str, *args: List[str]) -> List[str]:
    """mgr.py系のコマンドを生成する.

    Args:
        args(List[str]): "mgr.py 以降のコマンド

    Returns:
        List[str]: 実行結果
    """
    # リストを用意する
    ret = []
    if sys.platform == "win32":
        ret.append("mgr.py")
    else:
        ret.append("./mgr.py")

    # リストの末尾に、*argsのリストを加える
    ret.extend(*args)
    return ret


def _generate_command(*args: List[str]) -> List[str]:
    """コマンドを生成する.

    Args:
        args(List[str]): "コマンド

    Returns:
        List[str]: 実行結果
    """
    # リストを用意する
    ret: List[str] = []
    # リストの末尾に、*argsのリストを加える
    ret.extend(*args)
    return ret

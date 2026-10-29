"""プロセス実行モジュール."""
import logging
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

import chardet

import wasanbon_webframework.config.log_config  # noqa: F401

logger = logging.getLogger(__name__)


def start_process_return_string(command: List[str], stdin_str: Optional[str] = None) -> Tuple[int, str, str]:
    """コマンドを実行し、文字列を返す関数.

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    logger.info(f"command: {command}, stdin_str: {stdin_str}")
    if stdin_str is not None:
        # binder内のyamlの選択から一番上を選択するようstdinを渡す
        with tempfile.TemporaryFile("w") as f:
            f.write(f"{stdin_str}\n")
            f.seek(0)
            # コマンドを実行する
            if sys.platform == "win32":
                rtn = subprocess.run(command, capture_output=True, shell=True, stdin=f)
            else:
                rtn = subprocess.run(command, capture_output=True, stdin=f)
    else:
        # コマンドを実行する
        if sys.platform == "win32":
            rtn = subprocess.run(command, capture_output=True, shell=True)
        else:
            rtn = subprocess.run(command, capture_output=True)

    _stdout_encode = chardet.detect(rtn.stdout)
    stdout_encode = _stdout_encode["encoding"] if _stdout_encode["encoding"] is not None else "utf-8"
    _stderr_encode = chardet.detect(rtn.stderr)
    stderr_encode = _stderr_encode["encoding"] if _stderr_encode["encoding"] is not None else "utf-8"

    logger.info(f"stdout: {str(rtn.stdout)}")
    logger.info(f"stderr: {str(rtn.stderr)}")
    return (rtn.returncode, rtn.stdout.decode(stdout_encode), rtn.stderr.decode(stderr_encode))


def start_background_process_return_string(command: List[str], wait_flg: bool = False) -> int:
    """コマンドをバックグラウンド実行し、終了コードを返す関数.

    Returns:
        int: return_code
    """
    logger.info(f"command: {command}, wait_flg: {wait_flg}")
    # コマンドを実行する
    if sys.platform == "win32":
        rtn = subprocess.Popen(command, shell=True)
    else:
        rtn = subprocess.Popen(command)
    if wait_flg:
        out, err = rtn.communicate()
        logger.info("stdout: {!r}".format(out))
        logger.info("stderr: {!r}".format(err))

    logger.info(f"rtn.returncode: {rtn.returncode}")
    return rtn.returncode

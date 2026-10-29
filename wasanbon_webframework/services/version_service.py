"""versionサービスモジュール."""

from typing import Tuple

from ..services.wasanbon_util import _generate_wasanbon_admin_command
from .process_util import start_process_return_string


def get_wasanbon_version() -> Tuple[int, str, str]:
    """wasanbonのバージョンを確認する.

    $ wasanbon-admin.py version
    Args:
        None
    Returns:
        Dict: 実行結果{"platform version": output, "wasanbon version": output}
    """
    # オプションを指定して実行コマンドを生成する
    options = ["version"]

    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)

"""各APIで使用されるクラス."""

from enum import Enum


class WS(str, Enum):
    """Model to select Workspace."""

    dev = "dev"
    exec = "exec"

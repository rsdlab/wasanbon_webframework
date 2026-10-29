"""APIで利用する設定を管理するモジュール."""

import os

home_dir = os.path.expanduser("~")

WW_BASE_PATH = os.path.join(home_dir, "test_fw")
#WW_BASE_PATH = os.path.join(home_dir, "catkin_ws")
DEVELOP_WORKSPACE_BASE_PATH = os.path.join(WW_BASE_PATH, "src")
EXECUTE_WORKSPACE_BASE_PATH = os.path.join(WW_BASE_PATH, "execute_workspace")

DEBUG = False

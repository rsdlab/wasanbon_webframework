"""Logging設定を管理するモジュール."""
import logging
import logging.config
import os

target_path = os.path.join(os.path.dirname(__file__), "../logging.conf")
logging.config.fileConfig(target_path, disable_existing_loggers=False)

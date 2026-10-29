"""認証資格チェックモジュール."""
import base64
import binascii
import csv
import logging
import os
import re
import secrets

import yaml
from fastapi.requests import HTTPConnection
from starlette.authentication import AuthenticationBackend, AuthenticationError
from starlette.responses import PlainTextResponse, Response

import wasanbon_webframework.config.log_config  # noqa: F401
from wasanbon_webframework.config.config import WW_BASE_PATH

logger = logging.getLogger(__name__)


class BasicAuth(AuthenticationBackend):
    """Basic認証クラス."""

    no_auth_path = os.path.join(os.path.dirname(__file__), "../config/no_authentication_required_list.csv")
    no_auth_file = open(no_auth_path, "r")
    no_auth_list = list(csv.reader(no_auth_file))

    @staticmethod
    def default_on_error(conn: HTTPConnection, exc: Exception) -> Response:
        """例外発生時のデフォルト処理.

        Args:
            conn(HTTPConnection): 接続情報
            exc(Exception): 例外

        Returns:
            Response: レスポンス
        """
        logger.info(exc)
        return PlainTextResponse(str(exc.args[1]), status_code=exc.args[0])

    async def authenticate(self, request: HTTPConnection) -> None:
        """認証処理.

        Args:
            request(HTTPConnection): リクエスト
        """
        url = str(request.url)
        header = re.match(r"https?://[^/]+", url)
        if header is not None:
            router = url[header.end() :]
            if [router] in self.no_auth_list:
                return

        if "Authorization" in request.headers:
            auth = request.headers["Authorization"]
        elif "authorization" in request.headers:
            auth = request.headers["authorization"]
        else:
            raise AuthenticationError(401, "Invalid basic auth credentials")

        try:
            scheme, credentials = auth.split()
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationError(401, "Invalid basic auth credentials")

        username, _, password = decoded.partition(":")

        # user password資格確認
        user_file_path = os.path.join(WW_BASE_PATH, "user_info.yml")
        try:
            with open(user_file_path) as file:

                user_info = yaml.safe_load(file)
                if user_info is None:
                    user_info = {}

                correct_username = False
                correct_password = False

                if username in user_info.keys():
                    correct_username = True
                    correct_password = secrets.compare_digest(password, user_info[username])

                if not (correct_username and correct_password):
                    raise AuthenticationError(401, "Incorrect password")
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(500, f"failed to get user info: {e}")

        return

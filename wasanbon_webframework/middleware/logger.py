"""ロガー系のモジュール."""

from logging import getLogger
from typing import Any, Dict

from fastapi import Response
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

import wasanbon_webframework.config.log_config  # noqa: F401


class LoggerMiddleware(BaseHTTPMiddleware):
    """ロガーミドルウェア."""

    logger = getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """ログをファイル出力するミドルウェア.

        Args:
            request (Request): リクエスト
            call_next (Any): レスポンスを受け取るまで待機する関数

        Returns:
            Response: レスポンス
        """
        self.logger.info(request.url)  # URL
        self.logger.info(request.method)  # method
        self.logger.info(request.path_params)  # parm
        request_body = await request.body()
        await self.set_body(request, request_body)
        response = await call_next(request)
        self.logger.info(response.status_code)  # code
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            self.logger.info(request_body.decode())
            self.logger.info(response_body.decode())
        except BaseException:
            self.logger.info("failed to log request or response body")

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    async def set_body(self, request: Request, body: bytes) -> Dict[str, bytes]:
        """リクエストボディの型を整える.

        Args:
            request (Request): リクエストオブジェクト
            body (bytes): リクエストボディ

        Returns:
            Dict[str, bytes]: {"type": "http.request", "body": body}
        """

        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive

        return {}

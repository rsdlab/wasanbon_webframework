"""各APIで使用されるクラス."""

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class BinderUser(BaseModel):
    """Model for binder user."""

    username: str
    token: str

    @validator("username")
    def validate_username(cls, value: str) -> str:  # noqa: N805
        """ユーザー名の入力チェックを行う.

        Args:
            cls:クラス名
            value(str): 入力値

        Returns:
            str: 入力値 ※エラーの場合はHTTPExceptionを返却
        """
        if len(value) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User Name Unspecified: {value} validation error",
            )

        return value

    @validator("token")
    def validate_token(cls, value: str) -> str:  # noqa: N805
        """アクセストークンの入力チェックを行う.

        Args:
            cls:クラス名
            value(str): 入力値

        Returns:
            str: 入力値 ※エラーの場合はHTTPExceptionを返却
        """
        if len(value) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Token Unspecified: {value} validation error",
            )

        return value

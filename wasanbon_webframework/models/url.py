"""各APIで使用されるクラス."""
from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class URL(BaseModel):
    """Model for URL."""

    url: str

    @validator("url")
    def validate_url(cls, value: str) -> str:  # noqa: N805
        """URLの入力チェックを行う.

        Args:
            cls:クラス名
            value(str): 入力値

        Returns:
            str: 入力値 ※エラーの場合はHTTPExceptionを返却
        """
        if len(value) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"URL Unspecified {value}")

        return value

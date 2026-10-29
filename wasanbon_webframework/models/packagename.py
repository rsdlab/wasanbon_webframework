"""各APIで使用されるクラス."""

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class PackageName(BaseModel):
    """Model for Package Name."""

    name: str

    @validator("name")
    def validate_packagename(cls, value: str) -> str:  # noqa: N805
        """パッケージ名の入力チェックを行う.

        Args:
            cls:クラス名
            value(str): 入力値

        Returns:
            str: 入力値 ※エラーの場合はHTTPExceptionを返却
        """
        if len(value) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Package Name Unspecified {value}"
            )

        return value

"""各APIで使用されるクラス."""

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class BinderName(BaseModel):
    """Model for binder name."""

    binder_name: str

    @validator("binder_name")
    def validate_bindername(cls, value: str) -> str:  # noqa: N805
        """バインダー名の入力チェックを行う.

        Args:
            cls:クラス名
            value(str): 入力値

        Returns:
            str: 入力値 ※エラーの場合はHTTPExceptionを返却
        """
        if len(value) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Binder Name Unspecified {value}"
            )

        return value

"""Workspaceを選択するパラメタで使用するEnum."""

from pydantic import BaseModel


class Commit(BaseModel):
    """Model for Commit Message."""

    comment: str

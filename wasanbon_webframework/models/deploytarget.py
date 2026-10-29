"""deployで使用されるクラス.."""

from pydantic import BaseModel, Field


class DeployTarget(BaseModel):
    """Model for deploy target."""

    rts_git_url: str = Field(min_length=1)
    commit_hash: str = Field(min_length=1)

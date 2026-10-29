"""バージョン確認に関するモジュール."""
import logging
from typing import Dict, Union

from fastapi import APIRouter, HTTPException

from wasanbon_webframework import get_version

from ..services.version_service import get_wasanbon_version

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["version"], dependencies=[])


@router.get(
    "/version",
    description="""
        Get Versions of wasanbon and wasanbon webframework.

        """,
)
def get_versions() -> Dict[str, Union[Dict[str, str], str]]:
    """wasanbon、wasanbon webframeworkのバージョンを確認する.

    Returns:
        Dict: { "platform version": os, "wasanbon version": version }
    """
    wasanbon_webframe_work_version = get_version()
    code, stdout, stderr = get_wasanbon_version()

    if code == 0:
        output = stdout.replace("\r\n", " ").split()

        return {
            "wasanbon version": {"platform version": output[2], "wasanbon version": output[5]},
            "wasanbon-webframework version": wasanbon_webframe_work_version,
        }
    else:
        raise HTTPException(status_code=500, detail={"stdout": stdout, "stderr": stderr})

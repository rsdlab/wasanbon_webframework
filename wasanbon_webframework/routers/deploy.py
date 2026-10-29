"""デプロイに関するモジュール."""
import logging
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status

import wasanbon_webframework.services.common_service as common_service
import wasanbon_webframework.services.deploy_service as service
from wasanbon_webframework.models.ws import WS

from ..models.deploytarget import DeployTarget

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deploy", tags=["deploy"], dependencies=[])


@router.post(
    "/{ws}/packages/deploy",
    description="""
        Deploy RTS to Execute Workspace on connection host.

        clone rts_git_url
        clone required RTC in RTS

        """,
)
def deploy(ws: WS, deploy_target: DeployTarget, request: Request) -> Dict[str, Optional[str]]:
    """接続hostのExecute WorkspaceにRTSをデプロイする.

    1. rts_git_urlをcloneする
    2. RTS内の必要なRTCをcloneする

    Args:
        rts_git_url(str): クローンするRTSのURL
        hash(str): クローンするハッシュ

    Returns:
        Dict: 実行結果
    """
    if common_service.is_write_workspace(ws):
        # 指定したWSが「dev」の場合は処理を終了する
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Develop workspace cannot be deployed")

    code, stdout, stderr = service.deploy(ws, deploy_target, request)

    if code == 0:
        return {"message": stdout}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"stdout": stdout, "stderr": stderr},
        )

# Author: Garam Mo
# Last Modified: 2026/06/21 by Garam Mo
#
# 역할: 태스크 기여도 엔드포인트
# 목적: POST /task/score → TaskScoreResponse

from fastapi import APIRouter
from api.schemas import TaskContributionRequest, TaskScoreResponse
from api.utils import to_action_item, to_team_settings

from engine import calc_task_contribution

router = APIRouter()


@router.post("/score", response_model=TaskScoreResponse)
def task_score(req: TaskContributionRequest) -> TaskScoreResponse:
    actions = [to_action_item(a) for a in req.actions]
    cfg     = to_team_settings(req.cfg)
    result  = calc_task_contribution(
        req.name, actions, cfg,
        team_avg_completed_weight=req.team_avg_completed_weight,
    )

    return TaskScoreResponse(
        name               = result.name,
        score              = result.score,
        total_actions      = result.total_actions,
        completed_actions  = result.completed_actions,
        completed_weight   = result.completed_weight,
        volume_score       = result.volume_score,
    )
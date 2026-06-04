# Author: Garam Mo
# Last Modified: 2026/06/04 by Garam Mo
#
# 역할: 최종 종합 기여도 엔드포인트
# 목적: POST /final/score → FinalScoreResponse

from fastapi import APIRouter
from api.schemas import FinalScoreRequest, FinalScoreResponse
from api.utils import to_team_settings

from engine import calc_final_score
from engine.models import CumulativeScore, TaskScore

router = APIRouter()


@router.post("/score", response_model=FinalScoreResponse)
def final_score(req: FinalScoreRequest) -> FinalScoreResponse:
    cfg = to_team_settings(req.cfg)

    cumulative = CumulativeScore(
        name           = req.cumulative_name,
        score          = req.cumulative_score,
        meeting_count  = req.cumulative_meeting_count,
        included_count = req.cumulative_included_count,
        excluded_count = req.cumulative_excluded_count,
    )
    task = TaskScore(
        name               = req.task_name,
        score              = req.task_score,
        total_actions      = req.task_total_actions,
        completed_actions  = req.task_completed_actions,
    )

    result = calc_final_score(cumulative, task, cfg, is_leader=req.is_leader)

    return FinalScoreResponse(
        name           = result.name,
        meeting_score  = result.meeting_score,
        task_score     = result.task_score,
        final          = result.final,
        weights_used   = result.weights_used,
        leader_applied = result.leader_applied,
    )

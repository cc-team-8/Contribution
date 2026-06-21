# Author: Garam Mo
# Last Modified: 2026/06/21 by Garam Mo
#
# 역할: 전체 파이프라인 엔드포인트 (단일 팀원의 최종 점수를 한 번에 계산)
# 목적: NestJS에서 여러 엔드포인트를 순서대로 호출하는 번거로움을 줄이기 위한 편의 엔드포인트

from fastapi import APIRouter
from api.schemas import FullPipelineRequest, FullPipelineResponse
from api.schemas import CumulativeScoreResponse, TaskScoreResponse, FinalScoreResponse
from api.utils import to_member_data, to_team_settings

from engine import (
    calc_meeting_score, calc_task_contribution,
    calc_cumulative_score, calc_final_score, collect_actions,
)

router = APIRouter()


@router.post("/score", response_model=FullPipelineResponse)
def full_pipeline(req: FullPipelineRequest) -> FullPipelineResponse:
    cfg      = to_team_settings(req.cfg)
    meetings = [to_member_data(m) for m in req.meetings]

    if not meetings:
        raise ValueError("meetings 는 최소 1개 이상이어야 합니다.")

    name = meetings[0].name

    # 1. 단일 회의 기여도 계산
    meeting_scores = [calc_meeting_score(m, cfg) for m in meetings]

    # 2. 회의 종합 기여도
    cumulative = calc_cumulative_score(name, meeting_scores, cfg)

    # 3. 태스크 기여도
    task = calc_task_contribution(
        name, collect_actions(meetings), cfg,
        team_avg_completed_weight=req.team_avg_completed_weight,
    )

    # 4. 최종 종합 기여도
    final = calc_final_score(cumulative, task, cfg, is_leader=req.is_leader)

    return FullPipelineResponse(
        name    = name,
        meeting = CumulativeScoreResponse(
            name           = cumulative.name,
            score          = cumulative.score,
            meeting_count  = cumulative.meeting_count,
            included_count = cumulative.included_count,
            excluded_count = cumulative.excluded_count,
        ),
        task = TaskScoreResponse(
            name               = task.name,
            score              = task.score,
            total_actions      = task.total_actions,
            completed_actions  = task.completed_actions,
            completed_weight   = task.completed_weight,
            volume_score       = task.volume_score,
        ),
        final = FinalScoreResponse(
            name           = final.name,
            meeting_score  = final.meeting_score,
            task_score     = final.task_score,
            final          = final.final,
            weights_used   = final.weights_used,
            leader_applied = final.leader_applied,
        ),
    )

# Author: Garam Mo
# Last Modified: 2026/06/04 by Garam Mo
#
# 역할: 회의 종합 기여도 엔드포인트
# 목적: POST /cumulative/score → CumulativeScoreResponse

from fastapi import APIRouter
from api.schemas import CumulativeScoreRequest, CumulativeScoreResponse
from api.utils import to_team_settings

from engine import calc_cumulative_score
from engine.models import MeetingScore, ReliabilityLabel

router = APIRouter()


@router.post("/score", response_model=CumulativeScoreResponse)
def cumulative_score(req: CumulativeScoreRequest) -> CumulativeScoreResponse:
    cfg = to_team_settings(req.cfg)

    # MeetingScoreItem → MeetingScore 변환
    meeting_scores = [
        MeetingScore(
            name                 = m.name,
            meeting_id           = m.meeting_id,
            meeting_total_sec    = m.meeting_total_sec,
            speech_score         = None,
            attend_score         = None,
            meeting_contribution = m.meeting_contribution,
            reliability          = ReliabilityLabel.HIGH,
            low_attend_flag      = False,
            weights_used         = {},
            is_official          = m.is_official,
            excused_absence      = m.excused_absence,
            absent               = m.absent,
        )
        for m in req.meeting_scores
    ]

    result = calc_cumulative_score(req.name, meeting_scores, cfg)

    return CumulativeScoreResponse(
        name           = result.name,
        score          = result.score,
        meeting_count  = result.meeting_count,
        included_count = result.included_count,
        excluded_count = result.excluded_count,
    )

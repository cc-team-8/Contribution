# Author: Garam Mo
# Last Modified: 2026/06/04 by Garam Mo
#
# 역할: 단일 회의 기여도 엔드포인트
# 목적: POST /meeting/score → MeetingScoreResponse

from fastapi import APIRouter
from api.schemas import MeetingScoreRequest, MeetingScoreResponse
from api.utils import to_member_data, to_team_settings

from engine import calc_meeting_score

router = APIRouter()


@router.post("/score", response_model=MeetingScoreResponse)
def meeting_score(req: MeetingScoreRequest) -> MeetingScoreResponse:
    data   = to_member_data(req.data)
    cfg    = to_team_settings(req.cfg)
    result = calc_meeting_score(data, cfg)

    return MeetingScoreResponse(
        name                 = result.name,
        meeting_id           = result.meeting_id,
        meeting_total_sec    = result.meeting_total_sec,
        speech_score         = result.speech_score,
        attend_score         = result.attend_score,
        meeting_contribution = result.meeting_contribution,
        reliability          = result.reliability.value,
        low_attend_flag      = result.low_attend_flag,
        weights_used         = result.weights_used,
        is_official          = result.is_official,
        excused_absence      = result.excused_absence,
        absent               = result.absent,
    )

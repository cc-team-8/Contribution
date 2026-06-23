# Author: Garam Mo
# Last Modified: 2026/06/23 by Garam Mo
#
# 역할: /pipeline/score 라우트(api/routes/pipeline.py) 테스트
# 목적: 응답에 포함된 meeting_scores(회의별 상세, attend_score 등)가 올바른지 검증.
#       FastAPI 서버를 실제로 띄우지 않고 라우트 함수를 직접 호출(httpx 의존 없음).

import pytest
from api.routes.pipeline import full_pipeline
from api.schemas import FullPipelineRequest, MemberMeetingDataSchema, TeamSettingsSchema


def _req(meetings: list[MemberMeetingDataSchema], cfg: TeamSettingsSchema = None) -> FullPipelineRequest:
    return FullPipelineRequest(
        meetings=meetings,
        cfg=cfg or TeamSettingsSchema(),
    )


# 응답에 meeting_scores가 채워지고, 입력 회의 수와 길이가 일치하는지
def test_meeting_scores_present_and_matches_input_count():
    meetings = [
        MemberMeetingDataSchema(
            name="A", meeting_id="m1",
            meeting_total_sec=3600, actual_attend_sec=3600, late_sec=0,
        ),
        MemberMeetingDataSchema(
            name="A", meeting_id="m2",
            meeting_total_sec=3000, actual_attend_sec=3000, late_sec=0,
        ),
    ]
    res = full_pipeline(_req(meetings))
    assert len(res.meeting_scores) == 2
    assert {ms.meeting_id for ms in res.meeting_scores} == {"m1", "m2"}


# attend_score는 화면의 "출석" 표시가 의존하는 핵심 필드 — 사유 지각 승인 시
# punct_score가 면제되어 attend_score가 1.0(만점)이 되는지 확인.
# (NestJS 쪽 attendance_ratio는 지각 시간을 차감하지 않으므로 이 값을 써야 한다)
def test_attend_score_reflects_excused_late_waiver():
    cfg = TeamSettingsSchema(late_threshold_sec=300, late_max_sec=900)
    excused = MemberMeetingDataSchema(
        name="jh", meeting_id="m1",
        meeting_total_sec=3600, actual_attend_sec=3600, late_sec=720,
        excused_late=True,
    )
    unexcused = MemberMeetingDataSchema(
        name="jh", meeting_id="m1",
        meeting_total_sec=3600, actual_attend_sec=3600, late_sec=720,
        excused_late=False,
    )
    res_excused = full_pipeline(_req([excused], cfg))
    res_unexcused = full_pipeline(_req([unexcused], cfg))
    assert res_excused.meeting_scores[0].attend_score == pytest.approx(1.0)
    assert res_unexcused.meeting_scores[0].attend_score < 1.0


# 완전 결석(absent=True) → meeting_scores 에도 attend_score=None, absent=True로 반영
def test_attend_score_none_when_absent():
    m = MemberMeetingDataSchema(
        name="sy", meeting_id="m1",
        meeting_total_sec=3000, actual_attend_sec=0, absent=True,
    )
    res = full_pipeline(_req([m]))
    assert res.meeting_scores[0].attend_score is None
    assert res.meeting_scores[0].absent is True

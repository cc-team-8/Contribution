# Author: Garam Mo
# Last Modified: 2025/06/01 by Garam Mo
#
# 역할: 단일 회의 기여도 산출 (발언 + 참석)
# 목적: 회의 한 번에 대한 기여도를 계산하는 진입점

from engine.models import (
    MemberMeetingData, TeamSettings,
    MeetingScore, ReliabilityLabel,
)
from engine.axes.speech     import calc_speech_score
from engine.axes.attendance import calc_attendance_score
from engine.reliability     import get_reliability


def calc_meeting_score(
    data: MemberMeetingData,
    cfg:  TeamSettings = None,
) -> MeetingScore:
    """
    함수명: calc_meeting_score
    설명: 한 회의에서 한 팀원의 기여도(발언 + 참석)를 계산한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
     - cfg  (TeamSettings):      팀 설정. None 이면 기본값 사용
    출력:
     - (MeetingScore): 회의 기여도 결과
    """
    if cfg is None:
        cfg = TeamSettings()

    # 완전 결석 → 즉시 0점 반환
    if data.absent:
        return MeetingScore(
            name                 = data.name,
            meeting_id           = data.meeting_id,
            meeting_total_sec    = data.meeting_total_sec,
            speech_score         = None,
            attend_score         = None,
            meeting_contribution = 0.0,
            reliability          = ReliabilityLabel.LOW,
            low_attend_flag      = True,
            weights_used         = {},
            is_official          = data.is_official,
            excused_absence      = data.excused_absence,
            absent               = True,
        )

    # 1. 축별 점수 계산 (측정 불가 시 None)
    speech_s = calc_speech_score(data, cfg)
    attend_s = calc_attendance_score(data, cfg)

    axes = {
        "speech": (speech_s, cfg.weight_speech_in_meeting),
        "attend": (attend_s, cfg.weight_attend_in_meeting),
    }

    # 2. None 이 아닌 축만 추려서 가중치 재분배
    measurable     = {k: v for k, v in axes.items() if v[0] is not None}
    measured_count = len(measurable)
    total_weight   = sum(v[1] for v in measurable.values())

    if total_weight == 0 or measured_count == 0:
        # 측정 가능한 축이 없으면 0점
        meeting_contribution = 0.0
        weights_used         = {}
    else:
        meeting_contribution = sum(v[0] * v[1] for v in measurable.values()) / total_weight
        weights_used         = {k: round(v[1] / total_weight, 6) for k, v in measurable.items()}

    # 3. 최소 참여 기준 미달 시 비례 하향 조정
    attend_ratio = (
        data.actual_attend_sec / data.meeting_total_sec
        if data.meeting_total_sec > 0 else 0.0
    )
    low_attend = attend_ratio < cfg.min_attend_ratio
    if low_attend:
        meeting_contribution *= attend_ratio / cfg.min_attend_ratio  # 참여율 낮을수록 패널티 증가

    return MeetingScore(
        name                 = data.name,
        meeting_id           = data.meeting_id,
        meeting_total_sec    = data.meeting_total_sec,
        speech_score         = speech_s,
        attend_score         = attend_s,
        meeting_contribution = round(meeting_contribution, 4),
        reliability          = get_reliability(data, measured_count),
        low_attend_flag      = low_attend,
        weights_used         = weights_used,
        is_official          = data.is_official,
        excused_absence      = data.excused_absence,
        absent               = data.absent,
    )
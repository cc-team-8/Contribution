# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 3축 점수를 조합해 최종 종합 기여도 산출
# 목적: 가중치 재분배·저참여 하향·신뢰도 라벨을 한 곳에서 처리하는 진입점

from engine.models import (
    MemberMeetingData, TeamSettings,
    ContributionResult,
)
from engine.axes.task       import calc_task_score
from engine.axes.speech     import calc_speech_score
from engine.axes.attendance import calc_attendance_score
from engine.reliability     import get_reliability


def calc_contribution(
    data: MemberMeetingData,
    cfg:  TeamSettings = None,
) -> ContributionResult:
    """
    함수명: calc_contribution
    설명: 3축 점수를 합산해 종합 기여도를 반환한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
     - cfg  (TeamSettings):      팀 설정. None 이면 기본값 사용
    출력:
     - (ContributionResult): 종합 점수 및 상세 결과
    """
    if cfg is None:
        cfg = TeamSettings()

    # 1. 축별 점수 계산 (측정 불가 시 None)
    task_s   = calc_task_score(data)
    speech_s = calc_speech_score(data)
    attend_s = calc_attendance_score(data, cfg)

    # 2. 각 축의 (점수, 가중치) 묶음
    axes = {
        "task":   (task_s,   cfg.weight_task),
        "speech": (speech_s, cfg.weight_speech),
        "attend": (attend_s, cfg.weight_attend),
    }

    # 3. None 이 아닌 축만 추려서 가중치 재분배
    measurable     = {k: v for k, v in axes.items() if v[0] is not None}
    measured_count = len(measurable)
    total_weight   = sum(v[1] for v in measurable.values())

    if total_weight == 0 or measured_count == 0:
        # 측정 가능한 축이 하나도 없으면 0점
        composite    = 0.0
        weights_used = {}
    else:
        # Σ(점수 × 가중치) / Σ(적용된 가중치) 로 정규화
        composite    = sum(v[0] * v[1] for v in measurable.values()) / total_weight
        # 재분배 후 실제 적용 비율 (역추적용)
        weights_used = {k: round(v[1] / total_weight, 6) for k, v in measurable.items()}

    # 4. 최소 참여 기준 미달 시 비례 하향 조정
    attend_ratio = (
        data.actual_attend_sec / data.meeting_total_sec
        if data.meeting_total_sec > 0 else 0.0
    )
    low_attend = attend_ratio < cfg.min_attend_ratio
    if low_attend:
        composite *= attend_ratio / cfg.min_attend_ratio  # 참여율이 낮을수록 패널티 증가
        
    # 5. 팀장 보정 - 계산 완료 후 bonus 가산
    if data.is_leader:
        composite = min(1.0, composite + cfg.leader_bonus)

    return ContributionResult(
        name            = data.name,
        task_score      = task_s,
        speech_score    = speech_s,
        attend_score    = attend_s,
        composite       = round(composite, 4),
        reliability     = get_reliability(data, measured_count),
        low_attend_flag = low_attend,
        weights_used    = weights_used,
    )

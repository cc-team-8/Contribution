# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 태스크 완료 축 점수 계산 (완료율 + 마감 준수율)
# 목적: 액션 아이템 기반 기여도를 독립적으로 측정

from typing import Optional
from engine.models import MemberMeetingData, ActionItem, TeamSettings


# 마감 준수 점수표 — (days_late 상한, 점수) 리스트
DEADLINE_TABLES: dict[str, list[tuple[float, float]]] = {
    # 엄격 모드: 초과 시 빠르게 감점, 당일은 만점
    "strict": [
        (1.0, 30.0),
        (3.0, 10.0),
        (float("inf"), 0.0),
    ],
    # 표준 모드 (스펙 기준)
    "normal": [
        (1.0, 60.0),           # 1일 이내 초과
        (3.0, 30.0),           # 3일 이내 초과
        (float("inf"), 10.0),  # 그 이상
    ],
    # 관대 모드: 늦어도 어느 정도 인정
    "lenient": [
        (3.0, 80.0),
        (7.0, 50.0),
        (float("inf"), 20.0),
    ],
}

def _deadline_score(item: ActionItem, mode: str = "normal") -> float:
    """
    함수명: _deadline_score
    설명: 액션 아이템 한 개의 마감 준수 점수를 반환한다.
    입력:
     - item (ActionItem): 완료 여부와 마감 지연일을 담은 액션 아이템
     - mode (str):        마감 패널티 모드 - strict/normal/lenient
    출력:
     - (float): 마감 준수 점수 (0~100)
    """
    if not item.completed:
        return 0.0

    d = item.days_late

    if d is None:
        return 100.0  # 마감 정보 없으면 완료 만점
    if d <= 0:
        return 100.0  # 마감 전 또는 당일
    
    # 점수표에서 첫 번째로 해당하는 구간 반환
    table = DEADLINE_TABLES.get(mode, DEADLINE_TABLES["normal"])
    for threshold, score in table:
        if d <= threshold:
            return score
    return 0.0


def calc_task_score(
    data: MemberMeetingData,
    cfg:  TeamSettings = None,
) -> Optional[float]:    
    """
    함수명: calc_task_score
    설명: 태스크 완료 축 점수를 계산한다. 배정 액션이 없으면 측정 불가로 None 을 반환한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
    출력:
     - (float | None): 태스크 완료 축 점수 (0~1). 배정 액션 0개일 경우 None
    """
    if cfg is None:
        cfg = TeamSettings()
    
    if not data.actions:
        return None

    mode         = cfg.deadline_mode
    total_weight = sum(a.difficulty for a in data.actions) # 난이도 합산
    
    # 완료율: 완료한 액션의 난이도 합 / 전체 난이도 합
    completion_ratio = sum(
        a.difficulty for a in data.actions if a.completed
    ) / total_weight
 
    # 마감 준수율: 난이도 가중 평균 (0~1 정규화)
    deadline_avg = sum(
        _deadline_score(a, mode) * a.difficulty for a in data.actions
    ) / total_weight / 100.0
 
    # 내부 배분 50/50
    return completion_ratio * 0.5 + deadline_avg * 0.5
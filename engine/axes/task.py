# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 태스크 완료 축 점수 계산 (완료율 + 마감 준수율)
# 목적: 액션 아이템 기반 기여도를 독립적으로 측정

from typing import Optional
from engine.models import MemberMeetingData, ActionItem


def _deadline_score(item: ActionItem) -> float:
    """
    함수명: _deadline_score
    설명: 액션 아이템 한 개의 마감 준수 점수를 반환한다.
    입력:
     - item (ActionItem): 완료 여부와 마감 지연일을 담은 액션 아이템
    출력:
     - (float): 마감 준수 점수 (0~100)
                마감 전·당일 100 / 1일 초과 80 / 3일 초과 60 / 7일 초과 30 / 그 이상·미완료 0
    """
    if not item.completed:
        return 0.0

    d = item.days_late

    if d is None:
        return 100.0  # 마감 정보 없으면 완료 만점
    if d <= 0:
        return 100.0  # 마감 전 또는 당일
    if d <= 1:
        return 80.0
    if d <= 3:
        return 60.0
    if d <= 7:
        return 30.0
    return 0.0


def calc_task_score(data: MemberMeetingData) -> Optional[float]:
    """
    함수명: calc_task_score
    설명: 태스크 완료 축 점수를 계산한다. 배정 액션이 없으면 측정 불가로 None 을 반환한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
    출력:
     - (float | None): 태스크 완료 축 점수 (0~1). 배정 액션 0개일 경우 None
    """
    if not data.actions:
        return None

    total_weight = sum(a.difficulty for a in data.actions) # 난이도 합산
    
    # 완료율: 완료한 액션의 난이도 합 / 전체 난이도 합
    completion_ratio = sum(
        a.difficulty for a in data.actions if a.completed
    ) / total_weight
 
    # 마감 준수율: 난이도 가중 평균 (0~1 정규화)
    deadline_avg = sum(
        _deadline_score(a) * a.difficulty for a in data.actions
    ) / total_weight / 100.0
 
    # 내부 배분 50/50 (TODO: 09-미결정-사항 확정 후 비율 조정)
    return completion_ratio * 0.5 + deadline_avg * 0.5
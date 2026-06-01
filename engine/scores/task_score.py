# Author: Garam Mo
# Last Modified: 2025/06/01 by Garam Mo
#
# 역할: 전체 기간 액션 아이템 기반 태스크 기여도 산출
# 목적: 회의와 분리해 태스크 기여도를 독립적으로 계산

from typing import Optional
from engine.models import ActionItem, MemberMeetingData, TeamSettings, TaskScore
from engine.axes.task import _deadline_score
 
 
def collect_actions(meetings: list[MemberMeetingData]) -> list[ActionItem]:
    """
    함수명: collect_actions
    설명: 여러 회의의 MemberMeetingData 에서 액션 아이템을 모아 하나의 목록으로 반환한다.
    입력:
     - meetings (list[MemberMeetingData]): 회의 데이터 목록
    출력:
     - (list[ActionItem]): 전체 기간 액션 아이템 목록
    """
    return [action for m in meetings for action in m.actions]
 
 
def calc_task_contribution(
    name:    str,
    actions: list[ActionItem],
    cfg:     TeamSettings = None,
) -> TaskScore:
    """
    함수명: calc_task_contribution
    설명: 전체 기간 동안 배정된 액션 아이템 목록으로 태스크 기여도를 계산한다.
    입력:
     - name    (str):             팀원 이름
     - actions (list[ActionItem]): 전체 기간 액션 아이템 목록
     - cfg     (TeamSettings):    팀 설정. None 이면 기본값 사용
    출력:
     - (TaskScore): 태스크 기여도 결과
    """
    if cfg is None:
        cfg = TeamSettings()
 
    if not actions:
        return TaskScore(
            name               = name,
            score              = None,
            total_actions      = 0,
            completed_actions  = 0,
        )
 
    mode         = cfg.deadline_mode
    total_weight = sum(a.difficulty for a in actions)
 
    # 완료율: 완료한 액션의 난이도 합 / 전체 난이도 합
    completed_count  = sum(1 for a in actions if a.completed)
    completion_ratio = sum(
        a.difficulty for a in actions if a.completed
    ) / total_weight
 
    # 마감 준수율: 난이도 가중 평균 (0~1 정규화)
    deadline_avg = sum(
        _deadline_score(a, mode) * a.difficulty for a in actions
    ) / total_weight / 100.0
 
    score = completion_ratio * 0.5 + deadline_avg * 0.5
 
    return TaskScore(
        name               = name,
        score              = round(score, 4),
        total_actions      = len(actions),
        completed_actions  = completed_count,
    )
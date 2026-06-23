# Author: Garam Mo
# Last Modified: 2025/06/21 by Garam Mo
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
    name:                     str,
    actions:                  list[ActionItem],
    cfg:                      TeamSettings    = None,
    team_avg_completed_weight: Optional[float] = None,
) -> TaskScore:
    """
    함수명: calc_task_contribution
    설명: 전체 기간 동안 배정된 액션 아이템 목록으로 태스크 기여도를 계산한다.
    입력:
     - name                       (str):             팀원 이름
     - actions                    (list[ActionItem]): 전체 기간 액션 아이템 목록
     - cfg                        (TeamSettings):    팀 설정. None 이면 기본값 사용
     - team_avg_completed_weight  (float | None):    (사용 안 함, 하위 호환용) 무시됨
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

    # difficulty=0 인 액션이 있을 경우 단순 평균으로 폴백
    if total_weight <= 0:
        total_weight = len(actions)

    # 완료한 액션의 난이도 가중 합 (= 절대 완료량. 난이도가 높을수록, 개수가 많을수록 커짐)
    completed_count    = sum(1 for a in actions if a.completed)
    completed_weight   = sum(a.difficulty for a in actions if a.completed)

    # 완료율: 완료한 액션의 난이도 합 / 전체 난이도 합 (전부 완료해야 1.0)
    completion_ratio = completed_weight / total_weight

    # 마감 준수율: 난이도 가중 평균 (0~1 정규화). 미완료 액션은 0점이므로
    # 완료율과 마찬가지로 "다 끝내야" 1.0에 가까워진다.
    deadline_avg = sum(
        _deadline_score(a, mode) * a.difficulty for a in actions
    ) / total_weight / 100.0

    # completion_ratio·deadline_avg 50:50 — 둘 다 1.0이어야(=전부 완료 + 마감 준수)
    # score가 1.0이 된다.
    score = completion_ratio * 0.5 + deadline_avg * 0.5

    return TaskScore(
        name               = name,
        score              = round(score, 4),
        total_actions      = len(actions),
        completed_actions  = completed_count,
        completed_weight   = completed_weight,
        volume_score       = None,
    )
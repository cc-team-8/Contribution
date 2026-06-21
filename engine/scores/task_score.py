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
          completion_ratio(완료율)·deadline_avg(마감 준수율) 외에, 팀 평균 완료량 대비
          본인의 난이도 가중 완료량을 보는 volume_score를 추가로 반영한다.
          이렇게 해야 "받은 태스크가 적어 비율만 채운 사람"이 "더 많이, 더 어려운 태스크를
          완료한 사람"보다 점수가 높게 나오는 역전 현상을 막을 수 있다.
    입력:
     - name                       (str):             팀원 이름
     - actions                    (list[ActionItem]): 전체 기간 액션 아이템 목록
     - cfg                        (TeamSettings):    팀 설정. None 이면 기본값 사용
     - team_avg_completed_weight  (float | None):    팀 전체 멤버의 완료 난이도 가중 합 평균.
                                                      None 이면 비교 기준이 없다는 뜻으로
                                                      volume_score 를 점수에서 제외하고
                                                      completion_ratio·deadline_avg 두 축만
                                                      재분배해 계산한다 (하위 호환).
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

    # 완료율: 완료한 액션의 난이도 합 / 전체 난이도 합
    completion_ratio = completed_weight / total_weight

    # 마감 준수율: 난이도 가중 평균 (0~1 정규화)
    deadline_avg = sum(
        _deadline_score(a, mode) * a.difficulty for a in actions
    ) / total_weight / 100.0

    # 완료량 점수: 팀 평균 완료 난이도 가중 합 대비 본인 비율 (1.0 상한)
    # team_avg_completed_weight 가 없거나 0이면(비교 기준 없음) 이 축을 제외하고 재분배한다.
    volume_score: Optional[float] = None
    if team_avg_completed_weight is not None and team_avg_completed_weight > 0:
        volume_score = min(1.0, completed_weight / team_avg_completed_weight)

    axes: dict[str, tuple[float, float]] = {
        "completion": (completion_ratio, 1.0),
        "deadline":   (deadline_avg, 1.0),
    }
    if volume_score is not None:
        # completion·deadline 의 기존 50:50 비중을 유지한 채 volume 축을 추가하고
        # 셋을 합이 1이 되도록 재정규화한다.
        remaining = 1.0 - cfg.weight_volume_in_task
        axes["completion"] = (completion_ratio, remaining * 0.5)
        axes["deadline"]   = (deadline_avg, remaining * 0.5)
        axes["volume"]     = (volume_score, cfg.weight_volume_in_task)

    total_axis_weight = sum(w for _, w in axes.values())
    score = sum(v * w for v, w in axes.values()) / total_axis_weight

    return TaskScore(
        name               = name,
        score              = round(score, 4),
        total_actions      = len(actions),
        completed_actions  = completed_count,
        completed_weight   = completed_weight,
        volume_score       = round(volume_score, 4) if volume_score is not None else None,
    )
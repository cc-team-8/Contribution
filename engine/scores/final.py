# Author: Garam Mo
# Last Modified: 2025/06/01 by Garam Mo
#
# 역할: 회의 종합 기여도와 태스크 기여도를 합산해 최종 종합 기여도 산출
# 목적: 팀장 보정 포함, 최종 1개의 점수로 출력하는 마지막 단계

from engine.models import CumulativeScore, TaskScore, TeamSettings, FinalScore


def calc_final_score(
    cumulative: CumulativeScore,
    task:       TaskScore,
    cfg:        TeamSettings = None,
    is_leader:  bool         = False,
) -> FinalScore:
    """
    함수명: calc_final_score
    설명: 회의 종합 기여도와 태스크 기여도를 weight_task_in_final 비율로 합산해
          최종 종합 기여도를 반환한다.
    입력:
     - cumulative (CumulativeScore): 회의 종합 기여도
     - task       (TaskScore):       태스크 기여도
     - cfg        (TeamSettings):    팀 설정. None 이면 기본값 사용
     - is_leader  (bool):            팀장 여부 (기본 False)
    출력:
     - (FinalScore): 최종 종합 기여도 결과
    """
    if cfg is None:
        cfg = TeamSettings()

    task_weight    = cfg.weight_task_in_final
    meeting_weight = 1.0 - cfg.weight_task_in_final

    # 측정 가능한 축만 포함
    axes: dict[str, tuple[float, float]] = {}
    if cumulative.score is not None:
        axes["meeting"] = (cumulative.score, meeting_weight)
    if task.score is not None:
        axes["task"] = (task.score, task_weight)

    # 가중치 재분배
    total_weight = sum(v[1] for v in axes.values())

    if total_weight == 0 or not axes:
        final        = 0.0
        weights_used = {}
    else:
        final        = sum(v[0] * v[1] for v in axes.values()) / total_weight
        weights_used = {k: round(v[1] / total_weight, 6) for k, v in axes.items()}

    # 팀장 보정: 곱하기 방식 (1.0 상한 적용)
    leader_applied = False
    if is_leader and cfg.leader_bonus > 0:
        final          = min(1.0, final * (1.0 + cfg.leader_bonus))
        leader_applied = True

    return FinalScore(
        name           = cumulative.name,
        meeting_score  = cumulative.score,
        task_score     = task.score,
        final          = round(final, 4),
        weights_used   = weights_used,
        leader_applied = leader_applied,
    )
# Author: Garam Mo
# Last Modified: 2025/06/01 by Garam Mo
#
# 역할: 여러 회의의 기여도를 회의 시간 가중 평균으로 합산
# 목적: 다중 회의 환경에서 팀원별 회의 종합 기여도를 산출

from engine.models import MeetingScore, TeamSettings, CumulativeScore
 
 
def calc_cumulative_score(
    name:           str,
    meeting_scores: list[MeetingScore],
    cfg:            TeamSettings = None,
) -> CumulativeScore:
    """
    함수명: calc_cumulative_score
    설명: 여러 회의의 기여도를 회의 시간 가중 평균으로 합산해 누적 점수를 반환한다.
          아래 기준으로 누적 포함 여부를 결정한다:
            - 비정규 회의(is_official=False) 제외
            - 최소 회의 시간(min_meeting_sec) 미만 제외
            - 사유 결석(excused_absence=True): 누적에서 제외
            - 무단 결석(excused_absence=False): 0점으로 포함
    입력:
     - name           (str):               팀원 이름
     - meeting_scores (list[MeetingScore]): 단일 회의 기여도 목록
     - cfg            (TeamSettings):      팀 설정. None 이면 기본값 사용
    출력:
     - (CumulativeScore): 회의 종합 기여도 결과
    """
    if cfg is None:
        cfg = TeamSettings()
 
    # 1. 정규 회의 + 최소 시간 필터
    eligible = [
        m for m in meeting_scores
        if m.is_official and m.meeting_total_sec >= cfg.min_meeting_sec
    ]
 
    # 2. 누적 포함 목록 구성 (score 와 함께)
    included: list[tuple[MeetingScore, float]] = []
    excluded_count = 0
 
    for m in eligible:
        if m.absent:
            if m.excused_absence:
                # 사유 결석: 누적에서 제외
                excluded_count += 1
            else:
                # 무단 결석: 0점으로 포함
                included.append((m, 0.0))
        else:
            included.append((m, m.meeting_contribution))
 
    # 3. 누적 포함 회의가 없으면 0점
    if not included:
        return CumulativeScore(
            name           = name,
            score          = 0.0,
            meeting_count  = len(meeting_scores),
            included_count = 0,
            excluded_count = len(eligible),  # 정규 회의 전부 제외된 경우
        )
 
    # 4. 회의 시간 가중 평균
    total_time   = sum(m.meeting_total_sec for m, _ in included)
    weighted_sum = sum(score * m.meeting_total_sec for m, score in included)
 
    cumulative = weighted_sum / total_time if total_time > 0 else 0.0
 
    return CumulativeScore(
        name           = name,
        score          = round(cumulative, 4),
        meeting_count  = len(meeting_scores),
        included_count = len(included),
        excluded_count = excluded_count,
    )
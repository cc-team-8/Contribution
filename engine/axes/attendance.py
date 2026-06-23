# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 참석 축 점수 계산 (출석 비율 + 정시 점수)
# 목적: 회의 참여 성실도를 독립적으로 측정

from typing import Optional
from engine.models import MemberMeetingData, TeamSettings


def calc_attendance_score(
    data: MemberMeetingData,
    cfg:  TeamSettings = None,
) -> Optional[float]:
    """
    함수명: calc_attendance_score
    설명: 참석 축 점수를 계산한다. 출석 비율과 정시 점수의 평균으로 산출한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
     - cfg  (TeamSettings):      팀 설정 (허용 지각 비율/절대 지각 기준 참조)
    출력:
     - (float | None): 참석 축 점수 (0~1). 회의 총 시간 0 일 경우 None
    """
    # cfg를 넘지기 않으면 기본값 빠르게 호출
    if cfg is None:
        cfg = TeamSettings()
        
    if data.meeting_total_sec <= 0:
        return None

    # 출석 비율: 실제 참여 시간 / 회의 총 시간 (1.0 상한 적용)
    attend_ratio = min(1.0, data.actual_attend_sec / data.meeting_total_sec)

    if data.excused_late:
        # 사유 지각 승인: 지각 감점(정시 점수)만 면제. 출석 비율은 그대로 반영.
        punct_score = 1.0
    elif cfg.late_threshold_sec is not None:
        punct_score = _punct_score_absolute(
            late_sec         = data.late_sec,
            threshold_sec    = cfg.late_threshold_sec,
            max_sec          = cfg.late_max_sec,
        )
    else:
        punct_score = _punct_score_ratio(data, cfg)

    return (attend_ratio + punct_score) / 2.0


def _punct_score_ratio(data: MemberMeetingData, cfg: TeamSettings) -> float:
    """
    함수명: _punct_score_ratio
    설명: 구 방식 정시 점수. 회의 시간 대비 punctuality_grace_ratio 를 허용 한도로 보고
          선형 감점한다 (cfg.late_threshold_sec 미설정 시 사용).
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
     - cfg  (TeamSettings):      팀 설정
    출력:
     - (float): 정시 점수 (0~1)
    """
    # 허용 지각 한도 (초)
    grace_sec = data.meeting_total_sec * cfg.punctuality_grace_ratio

    if grace_sec <= 0:
        # grace_ratio = 0 설정 시 0 나누기 방지 → 1초라도 지각하면 바로 0점
        return 1.0 if data.late_sec == 0 else 0.0

    # 지각이 한도에 가까울수록 선형 감소, 한도 초과 시 0.0 고정
    return max(0.0, 1.0 - data.late_sec / grace_sec)


def _punct_score_absolute(
    late_sec:      float,
    threshold_sec: float,
    max_sec:       Optional[float],
) -> float:
    """
    함수명: _punct_score_absolute
    설명: 신 방식 정시 점수. 절대 시간(초) 기준으로 산정한다.
    입력:
     - late_sec      (float):         실제 지각 시간 (초)
     - threshold_sec (float):         지각 기준 (초) - 이 시간까지는 감점 없음
     - max_sec       (float | None):  지각 최대 인정 시간 (초) - None/threshold 이하면
                                       상한 없음(점근적 감쇠로 처리)
    출력:
     - (float): 정시 점수 (0~1)
    """
    threshold_sec = max(0.0, threshold_sec)

    if late_sec <= threshold_sec:
        return 1.0

    over = late_sec - threshold_sec

    if max_sec is not None and max_sec > threshold_sec:
        span = max_sec - threshold_sec
        return max(0.0, 1.0 - over / span)

    # 상한 없음: 점근적 감쇠 (0에는 도달하지 않되 계속 줄어듦)
    unit = threshold_sec if threshold_sec > 0 else 60.0
    return 1.0 / (1.0 + over / unit)

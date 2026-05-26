# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 기여도 산정에 사용되는 모든 데이터 구조체 정의
# 목적: 입력·출력·설정 타입을 한 곳에서 관리해 파일 간 의존성을 단순화

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ReliabilityLabel(str, Enum):
    """
    함수명: ReliabilityLabel
    설명: 기여도 측정 결과의 신뢰도 등급을 나타내는 열거형.
    출력:
     - HIGH   (str): 3축 모두 측정 + 회의 30분 이상 + 오디오 손실 5% 미만
     - MEDIUM (str): 2축 측정 또는 회의 15~30분 또는 일부 캡처 손실
     - LOW    (str): 1축 이하 또는 회의 15분 미만 또는 캡처 손실 다수
    """
    HIGH   = "High"
    MEDIUM = "Medium"
    LOW    = "Low"


@dataclass
class TeamSettings:
    """
    함수명: TeamSettings
    설명: 팀별 조정 가능 설정. 기본값 = 06-기여도-산정.md 스펙 기본값.
    입력:
     - weight_task             (float): 태스크 완료 축 가중치 (기본 0.50)
     - weight_speech           (float): 발언 비중 축 가중치 (기본 0.30)
     - weight_attend           (float): 참석 축 가중치 (기본 0.10)
     - min_attend_ratio        (float): 최소 참여 기준 비율 (기본 0.40)
     - punctuality_grace_ratio (float): 허용 지각 비율 - 회의 시간 대비 (기본 0.10)
     - absence_exclude_excused (bool):  사유 결석 제외 여부 (기본 False)
    """
    weight_task:             float = 0.50
    weight_speech:           float = 0.30
    weight_attend:           float = 0.10

    min_attend_ratio:        float = 0.40
    punctuality_grace_ratio: float = 0.10
    absence_exclude_excused: bool  = False


@dataclass
class ActionItem:
    """
    함수명: ActionItem
    설명: 단일 액션 아이템의 완료 여부와 마감 준수 정보를 담는 구조체.
    입력:
     - completed (bool):           완료 여부
     - days_late (float | None):   마감 기준 지연일
                                   음수 = 마감 전, 0 = 당일, 양수 = 초과
                                   None = 마감 정보 없음 (완료 시 만점 처리)
    """
    completed:  bool
    days_late:  Optional[float] = None


@dataclass
class MemberMeetingData:
    """
    함수명: MemberMeetingData
    설명: 한 회의에서 한 팀원의 원시 데이터. 각 축 계산 함수의 단일 입력 타입.
    입력:
     - name               (str):              팀원 이름
     - meeting_total_sec  (float):            회의 총 시간 (초)
     - actual_attend_sec  (float):            실제 참여 시간 - 자리비움 제외 (초)
     - late_sec           (float):            지각한 시간 (초, 기본 0)
     - own_chars          (int):              본인 발언 글자수
     - total_chars_during (int):              본인 참여 시간 내 전체 참여자 글자수
     - actions            (list[ActionItem]): 배정된 액션 아이템 목록
     - audio_loss_pct     (float):            오디오 캡처 손실 % (기본 0)
     - excused_absence    (bool):             사유 결석 여부 (기본 False)
    """
    name: str

    # 참석 축
    meeting_total_sec:  float
    actual_attend_sec:  float
    late_sec:           float = 0.0

    # 발언 축
    own_chars:          int   = 0
    total_chars_during: int   = 0

    # 태스크 축
    actions: list[ActionItem] = field(default_factory=list)

    # 메타
    audio_loss_pct:  float = 0.0
    excused_absence: bool  = False


@dataclass
class ContributionResult:
    """
    함수명: ContributionResult
    설명: calc_contribution 의 최종 출력. 종합 점수와 역추적에 필요한 정보를 담는 구조체.
    입력:
     - name            (str):              팀원 이름
     - task_score      (float | None):     태스크 완료 축 점수 - None 이면 측정 불가
     - speech_score    (float | None):     발언 비중 축 점수 - None 이면 측정 불가
     - attend_score    (float | None):     참석 축 점수 - None 이면 측정 불가
     - composite       (float):            종합 점수 (0~1)
     - reliability     (ReliabilityLabel): 신뢰도 등급
     - low_attend_flag (bool):             최소 참여 기준 미달 여부
     - weights_used    (dict):             실제 적용된 가중치 - 재분배 후
    """
    name:            str
    task_score:      Optional[float]
    speech_score:    Optional[float]
    attend_score:    Optional[float]
    composite:       float
    reliability:     ReliabilityLabel
    low_attend_flag: bool
    weights_used:    dict

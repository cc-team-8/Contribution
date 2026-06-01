# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
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
     - HIGH   (str): 2축 모두 측정 + 회의 30분 이상 + 오디오 손실 5% 미만
     - MEDIUM (str): 1축 측정 또는 회의 15~30분 또는 일부 캡처 손실
     - LOW    (str): 0축 측정 또는 회의 15분 미만 또는 캡처 손실 다수
    """
    HIGH   = "High"
    MEDIUM = "Medium"
    LOW    = "Low"
    
 
@dataclass
class TeamSettings:
    """
    함수명: TeamSettings
    설명: 팀별 조정 가능 설정. 기본값 = 스펙 기본값.
    입력:
     - weight_speech_in_meeting (float): 회의 내 발언 비중 (기본 0.75)
     - weight_attend_in_meeting (float): 회의 내 참석 비중 (기본 0.25)
     - weight_task_in_final     (float): 최종 점수에서 태스크 비중 (기본 0.50, 생성 시에만 설정)
     - min_attend_ratio         (float): 최소 참여 기준 비율 (기본 0.40)
     - punctuality_grace_ratio  (float): 허용 지각 비율 - 회의 시간 대비 (기본 0.10)
     - absence_grace_sec        (float): 자리비움 인정 시간 초 (기본 30.0, 데이터 수집 레이어용)
     - leader_bonus             (float): 팀장 보정 계수 - final × (1 + n) (기본 0.2)
     - action_chars_limit       (int):   발언 1회 글자수 상한 (기본 500)
     - deadline_mode            (str):   마감 패널티 모드 - strict/normal/lenient (기본 normal)
     - min_meeting_sec          (float): 누적 포함 최소 회의 시간 초 (기본 300 = 5분)
     - score_visibility         (str):   기여도 공개 범위 - all/self/leader (기본 all, 표시 정책)
    """
    # 회의 내 가중치
    weight_speech_in_meeting: float = 0.75
    weight_attend_in_meeting: float = 0.25
 
    # 최종 합산 비율 (그룹 생성 시에만 설정)
    weight_task_in_final: float = 0.50
 
    # 참석 설정
    min_attend_ratio:        float = 0.40
    punctuality_grace_ratio: float = 0.10
    absence_grace_sec:       float = 30.0   # 자리비움 인정 시간 (데이터 수집 레이어용)
 
    # 팀장 보정
    leader_bonus: float = 0.2   # final × (1 + leader_bonus), 기본 0.2
 
    # 발언 설정
    action_chars_limit: int = 500   # 발언 1회 글자수 상한
 
    # 마감 모드
    deadline_mode: str = "normal"   # strict / normal / lenient
 
    # 누적 설정
    min_meeting_sec: float = 300.0  # 5분 미만 회의 누적 제외
 
    # 공개 범위 (계산 로직 아닌 표시 정책)
    score_visibility: str = "all"   # all / self / leader
    
 
@dataclass
class ActionItem:
    """
    함수명: ActionItem
    설명: 단일 액션 아이템의 완료 여부, 마감 준수, 난이도 정보를 담는 구조체.
    입력:
     - completed    (bool):           완료 여부
     - days_late    (float | None):   마감 기준 지연일
                                      음수 = 마감 전, 0 = 당일, 양수 = 초과
                                      None = 마감 정보 없음 (완료 시 만점 처리)
     - difficulty   (int):            난이도 - 1=하, 2=중(기본), 3=상
     - assigned_at  (str | None):     배정 시점 ISO 날짜 (기간 필터링용)
    """
    completed:   bool
    days_late:   Optional[float] = None
    difficulty:  int             = 2     # 1=하, 2=중(기본), 3=상
    assigned_at: Optional[str]   = None  # ISO 날짜 (예: "2025-01-15")
 
 
@dataclass
class MemberMeetingData:
    """
    함수명: MemberMeetingData
    설명: 한 회의에서 한 팀원의 원시 데이터.
    입력:
     - name               (str):   팀원 이름
     - meeting_id         (str):   회의 고유 식별자
     - meeting_total_sec  (float): 회의 총 시간 초
     - actual_attend_sec  (float): 실제 참여 시간 초 - 자리비움 제외
     - late_sec           (float): 지각한 시간 초 (기본 0)
     - own_chars          (int):   본인 발언 총 글자수
     - utterance_count    (int):   본인 발언 횟수 - 글자수 상한 적용용 (기본 1)
     - total_chars_during (int):   본인 참여 시간 내 전체 참여자 글자수
     - team_size          (int):   회의 참여 팀원 수 - 발언 기대치 계산용 (기본 1)
     - audio_loss_pct     (float): 오디오 캡처 손실 % (기본 0)
     - speech_confidence  (float): 음성인식 신뢰도 0~1 (기본 1.0)
     - excused_absence    (bool):  사유 결석 여부 (기본 False)
     - absent             (bool):  완전 결석 여부 - 한 번도 참여 안 함 (기본 False)
     - is_official        (bool):  정규 회의 여부 - 누적 포함 판단용 (기본 True)
     - is_leader          (bool):  팀장 여부 (기본 False)
     - actions            (list[ActionItem]): 이 회의에서 배정된 액션 아이템 목록 (기본 빈 리스트)
    """
    name:        str
    meeting_id:  str
 
    # 참석 축
    meeting_total_sec: float
    actual_attend_sec: float
    late_sec:          float = 0.0
 
    # 발언 축
    own_chars:          int   = 0
    utterance_count:    int   = 1
    total_chars_during: int   = 0
    team_size:          int   = 1
 
    # 메타
    audio_loss_pct:    float = 0.0
    speech_confidence: float = 1.0
    excused_absence:   bool  = False
    absent:            bool  = False
    is_official:       bool  = True
    is_leader:         bool  = False
 
    # 태스크 — 이 회의에서 배정된 액션 목록 (태스크 기여도 계산 시 모아서 사용)
    actions: list["ActionItem"] = field(default_factory=list)
 
 
@dataclass
class MeetingScore:
    """
    함수명: MeetingScore
    설명: 단일 회의의 기여도 결과 (발언 + 참석).
    입력:
     - name                 (str):              팀원 이름
     - meeting_id           (str):              회의 식별자
     - meeting_total_sec    (float):            회의 총 시간 초
     - speech_score         (float | None):     발언 점수 - None 이면 측정 불가
     - attend_score         (float | None):     참석 점수 - None 이면 측정 불가
     - meeting_contribution (float):            회의 기여도 (0~1)
     - reliability          (ReliabilityLabel): 신뢰도 등급
     - low_attend_flag      (bool):             최소 참여 기준 미달 여부
     - weights_used         (dict):             실제 적용 가중치 - 재분배 후
     - is_official          (bool):             정규 회의 여부
     - excused_absence      (bool):             사유 결석 여부
     - absent               (bool):             완전 결석 여부
    """
    name:                 str
    meeting_id:           str
    meeting_total_sec:    float
    speech_score:         Optional[float]
    attend_score:         Optional[float]
    meeting_contribution: float
    reliability:          ReliabilityLabel
    low_attend_flag:      bool
    weights_used:         dict
    is_official:          bool
    excused_absence:      bool
    absent:               bool
 
 
@dataclass
class TaskScore:
    """
    함수명: TaskScore
    설명: 전체 기간 액션 아이템 기반 태스크 기여도 결과.
    입력:
     - name              (str):           팀원 이름
     - score             (float | None):  태스크 기여도 - None 이면 액션 없음
     - total_actions     (int):           전체 액션 수
     - completed_actions (int):           완료된 액션 수
    """
    name:               str
    score:              Optional[float]
    total_actions:      int
    completed_actions:  int
 
 
@dataclass
class CumulativeScore:
    """
    함수명: CumulativeScore
    설명: 여러 회의의 기여도를 회의 시간 가중 평균으로 합산한 누적 결과.
    입력:
     - name           (str):   팀원 이름
     - score          (float): 회의 종합 기여도 (0~1)
     - meeting_count  (int):   전체 회의 수
     - included_count (int):   누적에 포함된 회의 수
     - excluded_count (int):   누적에서 제외된 회의 수 (사유 결석 등)
    """
    name:           str
    score:          float
    meeting_count:  int
    included_count: int
    excluded_count: int
 
 
@dataclass
class FinalScore:
    """
    함수명: FinalScore
    설명: 회의 종합 기여도와 태스크 기여도를 합산한 최종 종합 기여도.
    입력:
     - name           (str):            팀원 이름
     - meeting_score  (float):          회의 종합 기여도
     - task_score     (float | None):   태스크 기여도 - None 이면 액션 없음
     - final          (float):          최종 종합 점수 (0~1)
     - weights_used   (dict):           실제 적용 가중치
     - leader_applied (bool):           팀장 보정 적용 여부
    """
    name:           str
    meeting_score:  float
    task_score:     Optional[float]
    final:          float
    weights_used:   dict
    leader_applied: bool

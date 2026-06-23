# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 테스트 전반에서 공통으로 사용하는 데이터 생성 헬퍼 모음
# 목적: 반복되는 MemberMeetingData 생성 코드를 한 곳에서 관리

from engine import ActionItem, MemberMeetingData, TeamSettings, MeetingScore, ReliabilityLabel
 
 
def make_member(
    name:          str   = "김민준",
    meeting_id:    str   = "mtg-001",
    total_sec:     float = 3600,
    attend_sec:    float = 3600,
    late_sec:      float = 0.0,
    own_chars:     int   = 300,
    utterance_count: int = 1,
    total_chars:   int   = 1000,
    team_size:     int   = 4,
    audio_loss:    float = 0.0,
    speech_conf:   float = 1.0,
    excused:       bool  = False,
    excused_late:  bool  = False,
    absent:        bool  = False,
    is_official:   bool  = True,
    is_leader:     bool  = False,
    actions:       list  = None,
) -> MemberMeetingData:
    """
    함수명: make_member
    설명: 테스트용 MemberMeetingData 를 간편하게 생성하는 헬퍼.
    입력:
     - 기본값 따로 지정
    출력:
     - (MemberMeetingData): 테스트용 팀원 데이터
    """
    return MemberMeetingData(
        name               = name,
        meeting_id         = meeting_id,
        meeting_total_sec  = total_sec,
        actual_attend_sec  = attend_sec,
        late_sec           = late_sec,
        own_chars          = own_chars,
        utterance_count    = utterance_count,
        total_chars_during = total_chars,
        team_size          = team_size,
        audio_loss_pct     = audio_loss,
        speech_confidence  = speech_conf,
        excused_absence    = excused,
        excused_late       = excused_late,
        absent             = absent,
        is_official        = is_official,
        is_leader          = is_leader,
        actions            = actions if actions is not None else [],
    )
 
 
def make_action(
    completed:  bool         = True,
    days_late:  float | None = None,
    difficulty: int          = 2,
) -> ActionItem:
    """
    함수명: make_action
    설명: 테스트용 ActionItem 을 간편하게 생성하는 헬퍼.
    입력:
     - completed  (bool):           완료 여부 (기본 True)
     - days_late  (float | None):   마감 지연일 (기본 None = 마감 정보 없음)
     - difficulty (int):            난이도 1/2/3 (기본 2)
    출력:
     - (ActionItem): 테스트용 액션 아이템
    """
    return ActionItem(completed=completed, days_late=days_late, difficulty=difficulty)
 
 
def make_meeting_score(
    name:         str   = "김민준",
    meeting_id:   str   = "mtg-001",
    total_sec:    float = 3600,
    contribution: float = 0.7,
    is_official:  bool  = True,
    excused:      bool  = False,
    absent:       bool  = False,
) -> MeetingScore:
    """
    함수명: make_meeting_score
    설명: 누적 점수 테스트에서 사용할 MeetingScore 를 간편하게 생성하는 헬퍼.
    입력:
     - name         (str):   팀원 이름
     - meeting_id   (str):   회의 식별자
     - total_sec    (float): 회의 총 시간 초
     - contribution (float): 회의 기여도 (기본 0.7)
     - is_official  (bool):  정규 회의 여부 (기본 True)
     - excused      (bool):  사유 결석 여부 (기본 False)
     - absent       (bool):  완전 결석 여부 (기본 False)
    출력:
     - (MeetingScore): 테스트용 회의 기여도 결과
    """
    return MeetingScore(
        name                 = name,
        meeting_id           = meeting_id,
        meeting_total_sec    = total_sec,
        speech_score         = None if absent else 0.5,
        attend_score         = None if absent else 0.8,
        meeting_contribution = 0.0 if absent else contribution,
        reliability          = ReliabilityLabel.HIGH,
        low_attend_flag      = False,
        weights_used         = {} if absent else {"speech": 0.75, "attend": 0.25},
        is_official          = is_official,
        excused_absence      = excused,
        absent               = absent,
    )
 
 
DEFAULT_CFG = TeamSettings()

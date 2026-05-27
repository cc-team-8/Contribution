# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 테스트 전반에서 공통으로 사용하는 데이터 생성 헬퍼 모음
# 목적: 반복되는 MemberMeetingData 생성 코드를 한 곳에서 관리

from engine import ActionItem, MemberMeetingData, TeamSettings

# 아무 액션이 없는 팀원과 아무것도 안 넘겼을 때를 구분하기 위해 사용
_UNSET = object()


def make_member(
    name:         str   = "김민준",
    total_sec:    float = 3600,
    attend_sec:   float = 3600,
    late_sec:     float = 0.0,
    own_chars:    int   = 300,
    total_chars:  int   = 1000,
    team_size:    int   = 4,
    actions             = _UNSET,
    audio_loss:   float = 0.0,
    excused:      bool  = False,
) -> MemberMeetingData:
    """
    함수명: make_member
    설명: 테스트용 MemberMeetingData를 간편하게 생성하는 헬퍼.
    입력:
     - 기본 값 따로 지정
    출력:
     - (MemberMeetingData): 테스트용 팀원 데이터
    """
    
    # actions 를 명시하지 않으면 기본 3개짜리 혼합 셋을 사용한다.
    if actions is _UNSET:
        actions = [
            ActionItem(completed=True,  days_late=-1),
            ActionItem(completed=True,  days_late=0),
            ActionItem(completed=False, days_late=None),
        ]
    return MemberMeetingData(
        name               = name,
        meeting_total_sec  = total_sec,
        actual_attend_sec  = attend_sec,
        late_sec           = late_sec,
        own_chars          = own_chars,
        total_chars_during = total_chars,
        team_size          = team_size,
        actions            = actions,
        audio_loss_pct     = audio_loss,
        excused_absence    = excused,
    )


DEFAULT_CFG = TeamSettings()

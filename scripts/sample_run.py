# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 기여도 엔진 동작을 케이스별로 출력해 수동 확인
# 목적: 새 케이스를 빠르게 실험하거나 결과값을 눈으로 검토할 때 사용

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import ActionItem, MemberMeetingData, TeamSettings, calc_contribution


def print_result(label: str, result):
    print(f"\n{'─'*46}")
    print(f"  {label}")
    print(f"{'─'*46}")
    print(f"  종합 점수   : {result.composite:.4f}")
    print(f"  신뢰도      : {result.reliability.value}")
    print(f"  저참여 플래그: {result.low_attend_flag}")
    print(f"  태스크 점수  : {result.task_score}")
    print(f"  발언 점수   : {result.speech_score}")
    print(f"  참석 점수   : {result.attend_score}")
    print(f"  적용 가중치  : {result.weights_used}")


# 케이스 1: 모범 팀원
# 전 회의 참석 + 지각 없음 + 액션 모두 완료
# 높은 점수 기준선 확인
model_member = MemberMeetingData(
    name="김민준",
    meeting_total_sec=3600,
    actual_attend_sec=3600,
    late_sec=0,
    own_chars=350, total_chars_during=1000,
    team_size=4,
    actions=[
        ActionItem(completed=True, days_late=-2),
        ActionItem(completed=True, days_late=0),
        ActionItem(completed=True, days_late=1),
    ],
)
print_result("케이스 1 — 모범 팀원", calc_contribution(model_member))


# 케이스 2: 무임하차 유형
# 25% 참여 + 10분 지각 + 액션 대부분 미완료
# 무임하차 패널티 확인
freerider = MemberMeetingData(
    name="이무임",
    meeting_total_sec=3600,
    actual_attend_sec=900,    # 25% 참여
    late_sec=600,
    own_chars=30, total_chars_during=1000,
    team_size=4,
    actions=[
        ActionItem(completed=False),
        ActionItem(completed=False),
        ActionItem(completed=True, days_late=14),
    ],
)
print_result("케이스 2 — 무임하차 유형", calc_contribution(freerider))


# 케이스 3: 태스크 없는 참관자
# 전 회의 참석이지만 배정 액션 없음
# 채스크 축 제외 후 가중치 재분배 확인
observer = MemberMeetingData(
    name="박참관",
    meeting_total_sec=3600,
    actual_attend_sec=3600,
    late_sec=0,
    own_chars=200, total_chars_during=1000,
    team_size=4,
    actions=[],  # 배정 없음 → 태스크 측정 불가, 가중치 재분배
)
print_result("케이스 3 — 태스크 없는 참관자 (재분배)", calc_contribution(observer))


# 케이스 4: 팀 커스텀 가중치
# 케이스 1과 동일 인물, 태스크 가중치 70%로 올린 팀 설정
# 점수 변화 비교
cfg_custom = TeamSettings(weight_task=0.7, weight_speech=0.2, weight_attend=0.1)
print_result("케이스 4 — 모범 팀원 (태스크 중심 팀)", calc_contribution(model_member, cfg_custom))


# 케이스 5: 어려운 액션 완료 + 쉬운 액션 미완료
# -> 난이도 가중치 영향 확인
difficulty_member = MemberMeetingData(
    name="최난이",
    meeting_total_sec=3600,
    actual_attend_sec=3600,
    late_sec=0,
    own_chars=300, total_chars_during=1000,
    team_size=4,
    actions=[
        ActionItem(completed=True,  days_late=0,    difficulty=2.0),  # 어려운 액션 완료
        ActionItem(completed=False, days_late=None, difficulty=0.5),  # 쉬운 액션 미완료
    ],
)
print_result("케이스 5 — 난이도 가중치 (어려운 완료 + 쉬운 미완료)", calc_contribution(difficulty_member))


# 케이스 6: 케이스 1과 동일 조건 + 팀장 
# → leader_bonus 가산 확인
leader_member = MemberMeetingData(
    name="김팀장",
    meeting_total_sec=3600,
    actual_attend_sec=3600,
    late_sec=0,
    own_chars=350, total_chars_during=1000,
    team_size=4,
    is_leader=True,
    actions=[
        ActionItem(completed=True, days_late=-2),
        ActionItem(completed=True, days_late=0),
        ActionItem(completed=True, days_late=1),
    ],
)
print_result("케이스 6 — 팀장 보정 (케이스 1 + leader_bonus)", calc_contribution(leader_member))

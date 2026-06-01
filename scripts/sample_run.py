# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 기여도 엔진 동작을 케이스별로 출력해 수동 확인
# 목적: 단일 회의 → 누적 → 최종 전체 흐름을 10개 케이스로 검토

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import (
    ActionItem, MemberMeetingData, TeamSettings,
    calc_meeting_score, calc_task_contribution,
    calc_cumulative_score, calc_final_score, collect_actions,
)


def sep(title: str):
    print(f"\n{'═'*52}")
    print(f"  {title}")
    print(f"{'═'*52}")

def print_meeting(label: str, r):
    print(f"\n  ── {label}")
    print(f"     회의 기여도  : {r.meeting_contribution:.4f}")
    print(f"     신뢰도       : {r.reliability.value}")
    print(f"     발언 점수    : {r.speech_score}")
    print(f"     참석 점수    : {r.attend_score}")
    print(f"     저참여 플래그: {r.low_attend_flag}")

def print_final(label: str, r):
    print(f"\n  ── {label}")
    print(f"     최종 점수    : {r.final:.4f}")
    print(f"     회의 종합    : {r.meeting_score:.4f}")
    print(f"     태스크 기여도: {r.task_score}")
    print(f"     팀장 보정    : {r.leader_applied}")
    print(f"     적용 가중치  : {r.weights_used}")


def calc_single_final(m: MemberMeetingData, cfg: TeamSettings, is_leader: bool = False):
    """단일 회의 → 최종 점수까지 한 번에 계산하는 헬퍼"""
    meeting_score = calc_meeting_score(m, cfg)
    task_score    = calc_task_contribution(m.name, m.actions, cfg)
    cumulative    = calc_cumulative_score(m.name, [meeting_score], cfg)
    return calc_final_score(cumulative, task_score, cfg, is_leader=is_leader)


cfg = TeamSettings()


# ───────────────────────────────────────────────────────
# 케이스 1: 모범 팀원
# 60분 전체 참석 + 지각 없음 + 충분한 발언 + 액션 전부 마감 전 완료
# 기대: 최종 점수 높음
# ───────────────────────────────────────────────────────
sep("케이스 1 — 모범 팀원")
m1 = MemberMeetingData(
    name="김민준", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=400, utterance_count=2, total_chars_during=1200, team_size=4,
    actions=[
        ActionItem(completed=True, days_late=-2, difficulty=2),
        ActionItem(completed=True, days_late=-1, difficulty=3),
        ActionItem(completed=True, days_late=0,  difficulty=2),
    ],
)
print_meeting("단일 회의", calc_meeting_score(m1, cfg))
print_final("최종", calc_single_final(m1, cfg))


# ───────────────────────────────────────────────────────
# 케이스 2: 무임하차 유형
# 25% 참여 + 10분 지각 + 발언 거의 없음 + 액션 전부 미완료
# 기대: 최종 점수 낮음
# ───────────────────────────────────────────────────────
sep("케이스 2 — 무임하차 유형")
m2 = MemberMeetingData(
    name="이무임", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=900,
    late_sec=600,
    own_chars=30, utterance_count=1, total_chars_during=1000, team_size=4,
    actions=[
        ActionItem(completed=False, difficulty=2),
        ActionItem(completed=False, difficulty=2),
    ],
)
print_meeting("단일 회의", calc_meeting_score(m2, cfg))
print_final("최종", calc_single_final(m2, cfg))


# ───────────────────────────────────────────────────────
# 케이스 3: 완전 결석 (무단)
# 기대: 무단 결석 회의가 0점으로 누적에 포함되어 점수 낮아짐
# ───────────────────────────────────────────────────────
sep("케이스 3 — 무단 결석 (다중 회의 3회 중 1회 무단 결석)")
meetings_3 = [
    MemberMeetingData(
        name="박무단", meeting_id="mtg-1",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=350, utterance_count=2, total_chars_during=1000, team_size=4,
        actions=[ActionItem(completed=True, days_late=-1, difficulty=2)],
    ),
    MemberMeetingData(
        name="박무단", meeting_id="mtg-2",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=300, utterance_count=1, total_chars_during=1000, team_size=4,
        actions=[ActionItem(completed=True, days_late=0, difficulty=2)],
    ),
    MemberMeetingData(
        name="박무단", meeting_id="mtg-3",
        meeting_total_sec=3600, actual_attend_sec=0,
        absent=True, excused_absence=False,  # 무단 결석 → 0점으로 누적 포함
    ),
]
scores_3 = [calc_meeting_score(m, cfg) for m in meetings_3]
for i, r in enumerate(scores_3, 1):
    print_meeting(f"회의 {i}", r)
cum3   = calc_cumulative_score("박무단", scores_3, cfg)
task3  = calc_task_contribution("박무단", collect_actions(meetings_3), cfg)
final3 = calc_final_score(cum3, task3, cfg)
print(f"\n  ► 회의 종합: {cum3.score:.4f}  (포함 {cum3.included_count} / 전체 {cum3.meeting_count})")
print_final("최종", final3)


# ───────────────────────────────────────────────────────
# 케이스 4: 사유 결석 (다중 회의 3회 중 1회 사유 결석)
# 기대: 사유 결석 회의가 누적에서 제외되어 나머지 2회로만 평균
# 케이스 3과 비교 시 최종 점수가 더 높아야 함
# ───────────────────────────────────────────────────────
sep("케이스 4 — 사유 결석 (다중 회의 3회 중 1회 사유 결석)")
meetings_4 = [
    MemberMeetingData(
        name="최사유", meeting_id="mtg-1",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=350, utterance_count=2, total_chars_during=1000, team_size=4,
        actions=[ActionItem(completed=True, days_late=-1, difficulty=2)],
    ),
    MemberMeetingData(
        name="최사유", meeting_id="mtg-2",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=300, utterance_count=1, total_chars_during=1000, team_size=4,
        actions=[ActionItem(completed=True, days_late=0, difficulty=2)],
    ),
    MemberMeetingData(
        name="최사유", meeting_id="mtg-3",
        meeting_total_sec=3600, actual_attend_sec=0,
        absent=True, excused_absence=True,  # 사유 결석 → 누적에서 제외
    ),
]
scores_4 = [calc_meeting_score(m, cfg) for m in meetings_4]
for i, r in enumerate(scores_4, 1):
    print_meeting(f"회의 {i}", r)
cum4   = calc_cumulative_score("최사유", scores_4, cfg)
task4  = calc_task_contribution("최사유", collect_actions(meetings_4), cfg)
final4 = calc_final_score(cum4, task4, cfg)
print(f"\n  ► 회의 종합: {cum4.score:.4f}  (포함 {cum4.included_count} / 전체 {cum4.meeting_count}, 제외 {cum4.excluded_count})")
print_final("최종 (케이스 3보다 높아야 함)", final4)


# ───────────────────────────────────────────────────────
# 케이스 5: 발언 없음 (STT 전체 실패)
# 기대: speech 축 제외 후 attend 만으로 회의 기여도 계산
# ───────────────────────────────────────────────────────
sep("케이스 5 — 발언 없음 (STT 전체 실패)")
m5 = MemberMeetingData(
    name="정침묵", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=0, total_chars_during=0, team_size=4,
    actions=[ActionItem(completed=True, days_late=-1, difficulty=2)],
)
print_meeting("단일 회의 (발언 측정 불가 → attend 만)", calc_meeting_score(m5, cfg))
print_final("최종", calc_single_final(m5, cfg))


# ───────────────────────────────────────────────────────
# 케이스 6: 마감 지각 패널티 비교 (strict vs normal vs lenient)
# 기대: strict < normal < lenient
# ───────────────────────────────────────────────────────
sep("케이스 6 — 마감 모드 비교 (2일 지각 액션)")
m6_base = MemberMeetingData(
    name="모드테스트", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=300, utterance_count=1, total_chars_during=1000, team_size=4,
    actions=[ActionItem(completed=True, days_late=2, difficulty=2)],
)
for mode in ("strict", "normal", "lenient"):
    cfg_mode = TeamSettings(deadline_mode=mode)
    f = calc_single_final(m6_base, cfg_mode)
    print(f"\n  ── {mode:8s} → 최종: {f.final:.4f}  (태스크: {f.task_score:.4f})")


# ───────────────────────────────────────────────────────
# 케이스 7: 팀장 보정
# 발언 적고 태스크 일부 미완료인 조건에서 팀장 보정 차이 확인
# 기대: 팀장이 일반 팀원보다 높은 최종 점수
# ───────────────────────────────────────────────────────
sep("케이스 7 — 팀장 보정 비교")
m7 = MemberMeetingData(
    name="비교", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=150, utterance_count=1, total_chars_during=1000, team_size=4,  # 발언 적음
    actions=[
        ActionItem(completed=True,  days_late=2,    difficulty=2),  # 2일 지각
        ActionItem(completed=False, days_late=None, difficulty=2),  # 미완료
    ],
)
f_normal = calc_single_final(m7, cfg, is_leader=False)
f_leader = calc_single_final(m7, cfg, is_leader=True)
print(f"\n  ── 일반 팀원 최종: {f_normal.final:.4f}")
print(f"  ── 팀장    최종: {f_leader.final:.4f}  (leader_bonus={cfg.leader_bonus})")
print(f"  ── 차이         : +{f_leader.final - f_normal.final:.4f}")


# ───────────────────────────────────────────────────────
# 케이스 8: 다중 회의 누적 (3회 — 정상/지각/무단결석)
# 기대: 무단 결석이 0점으로 포함되어 누적 점수 낮아짐
# ───────────────────────────────────────────────────────
sep("케이스 8 — 다중 회의 누적 (3회)")
meetings_8 = [
    MemberMeetingData(
        name="김누적", meeting_id="mtg-1",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=400, utterance_count=2, total_chars_during=1200, team_size=4,
        actions=[ActionItem(completed=True, days_late=-1, difficulty=2)],
    ),
    MemberMeetingData(
        name="김누적", meeting_id="mtg-2",
        meeting_total_sec=1800, actual_attend_sec=1800,
        late_sec=300,
        own_chars=150, utterance_count=1, total_chars_during=600, team_size=4,
        actions=[ActionItem(completed=True, days_late=2, difficulty=1)],
    ),
    MemberMeetingData(
        name="김누적", meeting_id="mtg-3",
        meeting_total_sec=2700, actual_attend_sec=0,
        absent=True, excused_absence=False,
    ),
]
scores_8 = [calc_meeting_score(m, cfg) for m in meetings_8]
for i, r in enumerate(scores_8, 1):
    print_meeting(f"회의 {i}", r)

cum8   = calc_cumulative_score("김누적", scores_8, cfg)
task8  = calc_task_contribution("김누적", collect_actions(meetings_8), cfg)
final8 = calc_final_score(cum8, task8, cfg)
print(f"\n  ► 회의 종합 기여도: {cum8.score:.4f}  (포함 {cum8.included_count} / 전체 {cum8.meeting_count})")
print_final("최종 종합", final8)


# ───────────────────────────────────────────────────────
# 케이스 9: 짧은 회의 누적 제외
# 기대: 4분짜리 회의는 누적에서 빠짐
# ───────────────────────────────────────────────────────
sep("케이스 9 — 짧은 회의 누적 제외 (4분 회의)")
meetings_9 = [
    MemberMeetingData(
        name="김단회", meeting_id="mtg-long",
        meeting_total_sec=3600, actual_attend_sec=3600,
        own_chars=300, utterance_count=1, total_chars_during=1000, team_size=4,
        actions=[ActionItem(completed=True, days_late=-1, difficulty=2)],
    ),
    MemberMeetingData(
        name="김단회", meeting_id="mtg-short",
        meeting_total_sec=240,  # 4분 → 최소 기준(5분) 미달
        actual_attend_sec=240,
        own_chars=50, utterance_count=1, total_chars_during=200, team_size=4,
    ),
]
scores_9 = [calc_meeting_score(m, cfg) for m in meetings_9]
cum9   = calc_cumulative_score("김단회", scores_9, cfg)
task9  = calc_task_contribution("김단회", collect_actions(meetings_9), cfg)
final9 = calc_final_score(cum9, task9, cfg)
print(f"\n  전체 회의 수: {cum9.meeting_count}")
print(f"  누적 포함   : {cum9.included_count}  (4분 회의 제외)")
print_final("최종", final9)


# ───────────────────────────────────────────────────────
# 케이스 10: 태스크 중심 팀 vs 회의 중심 팀
# 동일 인물, 가중치만 다른 두 팀
# 기대: 태스크 잘 한 사람은 태스크 중심 팀에서 더 높은 점수
# ───────────────────────────────────────────────────────
sep("케이스 10 — 태스크 중심 팀 vs 회의 중심 팀")
cfg_task_heavy    = TeamSettings(weight_task_in_final=0.80)
cfg_meeting_heavy = TeamSettings(weight_task_in_final=0.20)

m10 = MemberMeetingData(
    name="한비교", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=150, utterance_count=1, total_chars_during=1000, team_size=4,
    actions=[
        ActionItem(completed=True, days_late=-1, difficulty=3),
        ActionItem(completed=True, days_late=-2, difficulty=3),
    ],
)
f_task    = calc_single_final(m10, cfg_task_heavy)
f_meeting = calc_single_final(m10, cfg_meeting_heavy)
print(f"\n  태스크 80% 팀 최종: {f_task.final:.4f}")
print(f"  회의  80% 팀 최종: {f_meeting.final:.4f}")
print(f"  (태스크={f_task.task_score:.4f}, 회의={f_task.meeting_score:.4f})")

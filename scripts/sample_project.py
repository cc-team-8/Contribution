# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 실제 팀 프로젝트 시뮬레이션 (4명, 10회 회의)
# 목적: 다양한 팀원 특성과 팀 설정에 따른 최종 점수 비교

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import (
    ActionItem, MemberMeetingData, TeamSettings,
    calc_meeting_score, calc_task_contribution,
    calc_cumulative_score, calc_final_score, collect_actions,
)


# ─────────────────────────────────────────────────────
# 팀원 프로필
# ─────────────────────────────────────────────────────
# A: 모범 팀원 — 발언 충분, 참석 완벽, 태스크 전부 마감 전 완료
# B: 팀장 (리더) — 발언 조금 적음, 참석 완벽, 태스크 6개 중 5개 완벽 + 1개 늦음
# C: 참석형 — 발언 적음, 참석 완벽, 태스크 6개 중 5개 완벽 + 1개 늦음
# D: 불성실형 — 발언 거의 없음, 가끔 지각, 태스크 6개 중 4개 완료

MEMBERS = ["김모범", "이팀장", "박참석", "최불성"]
TEAM_SIZE = 4

def make_meetings() -> dict[str, list[MemberMeetingData]]:
    """
    10회 회의 데이터 생성.
    반환값: {팀원명: [MemberMeetingData × 10]}
    """
    data = {name: [] for name in MEMBERS}

    for i in range(1, 11):
        mid = f"mtg-{i:02d}"
        dur = 3600 if i % 3 != 0 else 2700  # 대부분 60분, 일부 45분

        # ── 김모범: 모범 팀원 ─────────────────────────
        data["김모범"].append(MemberMeetingData(
            name="김모범", meeting_id=mid,
            meeting_total_sec=dur, actual_attend_sec=dur,
            own_chars=400, utterance_count=3, total_chars_during=1200, team_size=TEAM_SIZE,
            actions=[
                ActionItem(completed=True, days_late=-2, difficulty=3),
                ActionItem(completed=True, days_late=-1, difficulty=2),
            ],
        ))

        # ── 이팀장: 팀장 — 발언 조금 적고 태스크 1개 늦음 ──
        data["이팀장"].append(MemberMeetingData(
            name="이팀장", meeting_id=mid,
            meeting_total_sec=dur, actual_attend_sec=dur,
            own_chars=200, utterance_count=2, total_chars_during=1200, team_size=TEAM_SIZE,
            is_leader=True,
            actions=[
                ActionItem(completed=True, days_late=-1, difficulty=2),
                ActionItem(completed=True, days_late=2 if i == 5 else -1, difficulty=2),  # 5번 회의 액션 2일 지각
            ],
        ))

        # ── 박참석: 참석형 — 발언 적고 태스크 1개 늦음 ───
        data["박참석"].append(MemberMeetingData(
            name="박참석", meeting_id=mid,
            meeting_total_sec=dur, actual_attend_sec=dur,
            late_sec=0 if i % 4 != 0 else 200,  # 4번에 한 번 살짝 지각
            own_chars=150, utterance_count=1, total_chars_during=1200, team_size=TEAM_SIZE,
            actions=[
                ActionItem(completed=True, days_late=-1, difficulty=2),
                ActionItem(completed=True, days_late=3 if i == 7 else -1, difficulty=1),  # 7번 회의 액션 3일 지각
            ],
        ))

        # ── 최불성: 불성실형 — 가끔 결석, 발언 거의 없음 ──
        if i in (3, 8):
            # 2번 무단 결석
            data["최불성"].append(MemberMeetingData(
                name="최불성", meeting_id=mid,
                meeting_total_sec=dur, actual_attend_sec=0,
                absent=True, excused_absence=False,
            ))
        else:
            data["최불성"].append(MemberMeetingData(
                name="최불성", meeting_id=mid,
                meeting_total_sec=dur, actual_attend_sec=dur,
                late_sec=0 if i % 3 != 0 else 400,  # 가끔 지각
                own_chars=60, utterance_count=1, total_chars_during=1200, team_size=TEAM_SIZE,
                actions=[
                    ActionItem(completed=True  if i % 3 != 0 else False, days_late=-1, difficulty=2),
                    ActionItem(completed=True  if i % 4 != 0 else False, days_late=1,  difficulty=1),
                ],
            ))

    return data


def calc_member_final(
    name: str,
    meetings: list[MemberMeetingData],
    cfg: TeamSettings,
) -> dict:
    """팀원 한 명의 최종 점수 계산"""
    meeting_scores = [calc_meeting_score(m, cfg) for m in meetings]
    cumulative     = calc_cumulative_score(name, meeting_scores, cfg)
    task           = calc_task_contribution(name, collect_actions(meetings), cfg)
    is_leader      = any(m.is_leader for m in meetings)
    final          = calc_final_score(cumulative, task, cfg, is_leader=is_leader)
    return {
        "name":        name,
        "is_leader":   is_leader,
        "meeting_avg": cumulative.score,
        "task_score":  task.score,
        "final":       final.final,
        "leader_applied": final.leader_applied,
        "included":    cumulative.included_count,
        "total":       cumulative.meeting_count,
    }


def print_table(title: str, results: list[dict]):
    print(f"\n{'═'*62}")
    print(f"  {title}")
    print(f"{'═'*62}")
    print(f"  {'이름':<8} {'역할':<6} {'회의종합':>8} {'태스크':>8} {'최종점수':>8} {'포함회의':>8}")
    print(f"  {'─'*56}")
    for r in sorted(results, key=lambda x: x["final"], reverse=True):
        role = "팀장★" if r["is_leader"] else "팀원"
        leader_mark = " ←보정" if r["leader_applied"] else ""
        print(
            f"  {r['name']:<8} {role:<6} "
            f"{r['meeting_avg']:>8.4f} "
            f"{str(r['task_score'] or 0.0):>8} "
            f"{r['final']:>8.4f}{leader_mark}"
            f"   ({r['included']}/{r['total']}회)"
        )


# ─────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────
meetings_data = make_meetings()

# ── 설정 1: 기본값 (태스크 50 : 회의 50) ─────────────
cfg_default = TeamSettings()
results_default = [
    calc_member_final(name, meetings_data[name], cfg_default)
    for name in MEMBERS
]
print_table("설정 1 — 기본값 (태스크 50 : 회의 50)", results_default)

# ── 설정 2: 태스크 중점 (태스크 70 : 회의 30) ─────────
cfg_task = TeamSettings(weight_task_in_final=0.70)
results_task = [
    calc_member_final(name, meetings_data[name], cfg_task)
    for name in MEMBERS
]
print_table("설정 2 — 태스크 중점 (태스크 70 : 회의 30)", results_task)

# ── 설정 3: 회의 중점 (태스크 30 : 회의 70) ─────────
cfg_meeting = TeamSettings(weight_task_in_final=0.30)
results_meeting = [
    calc_member_final(name, meetings_data[name], cfg_meeting)
    for name in MEMBERS
]
print_table("설정 3 — 회의 중점 (태스크 30 : 회의 70)", results_meeting)

# ── 순위 변동 요약 ────────────────────────────────────
print(f"\n{'═'*62}")
print(f"  순위 변동 요약")
print(f"{'═'*62}")
print(f"  {'이름':<8} {'기본':>8} {'태스크중점':>10} {'회의중점':>10}")
print(f"  {'─'*40}")
for name in MEMBERS:
    d = next(r for r in results_default if r["name"] == name)
    t = next(r for r in results_task    if r["name"] == name)
    m = next(r for r in results_meeting if r["name"] == name)
    print(f"  {name:<8} {d['final']:>8.4f} {t['final']:>10.4f} {m['final']:>10.4f}")
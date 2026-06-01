# 무임하차 — 기여도 산정 엔진 v0.2

회의 기여도를 **4종류 점수**로 측정하는 순수 Python 엔진. 단일 회의부터 다중 회의 누적까지 지원합니다.

> 스펙: [`docs/spec/06-기여도-산정.md`](docs/spec/06-기여도-산정.md)
> 주석 가이드: [`docs/COMMENT_GUIDE.md`](docs/COMMENT_GUIDE.md)

---

## 📐 점수 4종류

| 번호 | 종류 | 설명 | 구현 위치 |
|---|---|---|---|
| 1 | 회의 기여도 | 단일 회의의 발언 + 참석 | `scores/meeting.py` |
| 2 | 태스크 기여도 | 전체 기간 액션 아이템 기반 | `scores/task_score.py` |
| 3 | 회의 종합 기여도 | 여러 회의를 시간 가중 평균으로 누적 | `scores/cumulative.py` |
| 4 | 종합 기여도 | 회의 종합 + 태스크를 합산한 최종 점수 | `scores/final.py` |

---

## 📁 폴더 구조

```
muimhaja-engine/
├── engine/
│   ├── __init__.py            ← 공개 API
│   ├── models.py              ← 데이터 구조체 전체
│   ├── reliability.py         ← 신뢰도 라벨 (High/Medium/Low/Absent)
│   ├── axes/
│   │   ├── task.py            ← 마감 점수 계산 (deadline_mode 지원)
│   │   ├── speech.py          ← 발언 비중 (글자수 상한 적용)
│   │   └── attendance.py      ← 참석 (출석 비율 + 정시 점수)
│   └── scores/
│       ├── meeting.py         ← 단일 회의 기여도
│       ├── task_score.py      ← 태스크 기여도 + collect_actions
│       ├── cumulative.py      ← 회의 종합 기여도 (누적)
│       └── final.py           ← 최종 종합 기여도
├── tests/
│   ├── fixtures.py
│   ├── test_task_axes.py
│   ├── test_speech_axes.py
│   ├── test_attendance_axes.py
│   ├── test_meeting.py
│   ├── test_task_score.py
│   ├── test_cumulative.py
│   └── test_final.py
├── docs/
│   ├── spec/06-기여도-산정.md
│   └── COMMENT_GUIDE.md
└── scripts/
    ├── sample_run.py          ← 기능별 케이스 확인
    └── sample_project.py      ← 4인 팀 10회 프로젝트 시뮬레이션
```

---

## ⚙️ 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## 🚀 빠른 시작

```bash
pytest                               # 전체 테스트 실행
python scripts/sample_run.py        # 기능별 케이스 출력
python scripts/sample_project.py    # 팀 프로젝트 시뮬레이션
```

---

## 💡 기본 사용법

```python
from engine import (
    ActionItem, MemberMeetingData, TeamSettings,
    calc_meeting_score, calc_task_contribution,
    calc_cumulative_score, calc_final_score, collect_actions,
)

cfg = TeamSettings(weight_task_in_final=0.50, leader_bonus=0.20)

# 1. 단일 회의 기여도 (액션은 회의에 저장)
data = MemberMeetingData(
    name="김민준", meeting_id="mtg-1",
    meeting_total_sec=3600, actual_attend_sec=3600,
    own_chars=350, utterance_count=2,
    total_chars_during=1000, team_size=4,
    actions=[
        ActionItem(completed=True,  days_late=-1, difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=2),
    ],
)
meeting = calc_meeting_score(data, cfg)

# 2. 태스크 기여도 (여러 회의의 액션을 모아서 계산)
all_actions = collect_actions([data, ...])
task = calc_task_contribution("김민준", all_actions, cfg)

# 3. 회의 종합 기여도 (여러 회의)
cumulative = calc_cumulative_score("김민준", [meeting, ...], cfg)

# 4. 최종 종합 기여도
final = calc_final_score(cumulative, task, cfg, is_leader=False)
print(final.final)  # 0~1
```

---

## 🔧 팀 설정 주요 항목

| 설정 | 기본값 | 설명 |
|---|---|---|
| `weight_task_in_final` | 0.50 | 최종에서 태스크 비중 (그룹 생성 시에만) |
| `deadline_mode` | `"normal"` | 마감 패널티 모드: `strict` / `normal` / `lenient` |
| `leader_bonus` | 0.20 | 팀장 보정 계수 — `final × (1 + n)` |
| `action_chars_limit` | 500 | 발언 1회 글자수 상한 |
| `min_attend_ratio` | 0.40 | 최소 참여 기준 비율 (미달 시 플래그만 표시) |
| `min_meeting_sec` | 300.0 | 누적 포함 최소 회의 시간 (초) |

---

## 🔮 추후 확장 포인트

- `api/` 추가 → FastAPI 엔드포인트로 래핑
- `engine/axes/` 에 새 파일 추가 → 새 측정 축 도입
- `engine/models.py` 의 `TeamSettings` → DB 모델로 교체

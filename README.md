# 무임하차 — 기여도 산정 엔진

회의 기여도를 **3축(태스크 완료 / 발언 비중 / 참석)** 으로 측정하는 순수 Python 엔진.  
> 스펙: [`docs/spec/06-기여도-산정.md`](docs/spec/06-기여도-산정.md)  
> 주석 가이드: [`docs/COMMENT_GUIDE.md`](docs/COMMENT_GUIDE.md)

## 📁 폴더 구조

```
muimhaja-engine/
├── engine/
│   ├── __init__.py        ← 공개 API (외부에서 여기만 import)
│   ├── models.py          ← 데이터 구조체 전체
│   ├── composite.py       ← 종합 점수 산출 (메인 진입점)
│   ├── reliability.py     ← 신뢰도 라벨
│   └── axes/
│       ├── task.py        ← 태스크 완료 축
│       ├── speech.py      ← 발언 비중 축
│       └── attendance.py  ← 참석 축
├── tests/
│   ├── fixtures.py        ← 공용 테스트 헬퍼
│   ├── test_task.py
│   ├── test_speech.py
│   ├── test_attendance.py
│   └── test_composite.py
├── docs/
│   ├── spec/
│   │   └── 06-기여도-산정.md
│   └── COMMENT_GUIDE.md   ← 주석 스타일 가이드
└── scripts/
    └── sample_run.py      ← 수동 동작 확인
```

## ⚙️ 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## 🚀 빠른 시작

```bash
pytest                          # 전체 테스트 실행
python scripts/sample_run.py    # 샘플 케이스 출력
```

## 💡 기본 사용법 예시

```python
from engine import ActionItem, MemberMeetingData, TeamSettings, calc_contribution

data = MemberMeetingData(
    name="김민준",
    meeting_total_sec=3600,
    actual_attend_sec=3600,
    late_sec=0,
    own_chars=300,
    total_chars_during=1000,
    actions=[
        ActionItem(completed=True,  days_late=-1),
        ActionItem(completed=True,  days_late=0),
        ActionItem(completed=False, days_late=None),
    ],
)

result = calc_contribution(data)
print(result.composite)    # 종합 점수 (0~1)
print(result.reliability)  # High / Medium / Low
```

## 🔧 팀 가중치 커스텀

```python
cfg = TeamSettings(weight_task=0.7, weight_speech=0.2, weight_attend=0.1)
result = calc_contribution(data, cfg)
```

## 🔮 추후 확장 포인트

- `api/` 추가 → FastAPI 엔드포인트로 래핑
- `engine/axes/` 에 새 파일 추가 → 새 측정 축 도입
- `engine/models.py` 의 `TeamSettings` → DB 모델로 교체

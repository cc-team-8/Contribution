# Author: Garam Mo
# Last Modified: 2026/06/21 by Garam Mo
#
# 역할: API 요청·응답 Pydantic 스키마 정의
# 목적: 엔진 dataclass 와 FastAPI 간의 타입 매핑

from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────
# 요청 스키마
# ─────────────────────────────────────────

class ActionItemSchema(BaseModel):
    completed:   bool
    days_late:   Optional[float] = None
    difficulty:  int             = 2
    assigned_at: Optional[str]   = None


class MemberMeetingDataSchema(BaseModel):
    name:               str
    meeting_id:         str
    meeting_total_sec:  float
    actual_attend_sec:  float
    late_sec:           float = 0.0
    own_chars:          int   = 0
    utterance_count:    int   = 1
    total_chars_during: int   = 0
    team_size:          int   = 1
    audio_loss_pct:     float = 0.0
    speech_confidence:  float = 1.0
    excused_absence:    bool  = False
    absent:             bool  = False
    is_official:        bool  = True
    is_leader:          bool  = False
    actions:            list[ActionItemSchema] = []


class TeamSettingsSchema(BaseModel):
    weight_speech_in_meeting: float = 0.75
    weight_attend_in_meeting: float = 0.25
    weight_task_in_final:     float = 0.50
    weight_volume_in_task:    float = 0.50
    min_attend_ratio:         float = 0.40
    punctuality_grace_ratio:  float = 0.10
    absence_grace_sec:        float = 30.0
    leader_bonus:             float = 0.2
    action_chars_limit:       int   = 500
    deadline_mode:            str   = "normal"
    min_meeting_sec:          float = 300.0
    score_visibility:         str   = "all"


# ── 회의 기여도 요청 ──────────────────────────────────
class MeetingScoreRequest(BaseModel):
    data: MemberMeetingDataSchema
    cfg:  TeamSettingsSchema = TeamSettingsSchema()


# ── 태스크 기여도 요청 ────────────────────────────────
class TaskContributionRequest(BaseModel):
    name:    str
    actions: list[ActionItemSchema]
    cfg:     TeamSettingsSchema = TeamSettingsSchema()
    # 팀 전체 멤버의 완료 난이도 가중 합 평균 — 완료량(volume_score) 계산 기준.
    # None 이면 비교 기준 없음으로 처리해 completion_ratio·deadline_avg 두 축만 사용.
    team_avg_completed_weight: Optional[float] = None


# ── 회의 종합 기여도 요청 ─────────────────────────────
class MeetingScoreItem(BaseModel):
    name:                 str
    meeting_id:           str
    meeting_total_sec:    float
    meeting_contribution: float
    is_official:          bool
    excused_absence:      bool
    absent:               bool


class CumulativeScoreRequest(BaseModel):
    name:           str
    meeting_scores: list[MeetingScoreItem]
    cfg:            TeamSettingsSchema = TeamSettingsSchema()


# ── 최종 종합 기여도 요청 ─────────────────────────────
class FinalScoreRequest(BaseModel):
    cumulative_name:           str
    cumulative_score:          float
    cumulative_meeting_count:  int
    cumulative_included_count: int
    cumulative_excluded_count: int
    task_name:                 str
    task_score:                Optional[float]
    task_total_actions:        int
    task_completed_actions:    int
    is_leader:                 bool = False
    cfg:                       TeamSettingsSchema = TeamSettingsSchema()


# ── 전체 파이프라인 요청 (단일 회의 → 최종) ──────────
class FullPipelineRequest(BaseModel):
    meetings: list[MemberMeetingDataSchema]
    is_leader: bool = False
    cfg:       TeamSettingsSchema = TeamSettingsSchema()
    # 팀 전체 멤버의 완료 난이도 가중 합 평균 — 완료량(volume_score) 계산 기준.
    # None 이면 비교 기준 없음으로 처리해 completion_ratio·deadline_avg 두 축만 사용.
    team_avg_completed_weight: Optional[float] = None


# ─────────────────────────────────────────
# 응답 스키마
# ─────────────────────────────────────────

class MeetingScoreResponse(BaseModel):
    name:                 str
    meeting_id:           str
    meeting_total_sec:    float
    speech_score:         Optional[float]
    attend_score:         Optional[float]
    meeting_contribution: float
    reliability:          str
    low_attend_flag:      bool
    weights_used:         dict
    is_official:          bool
    excused_absence:      bool
    absent:               bool


class TaskScoreResponse(BaseModel):
    name:               str
    score:              Optional[float]
    total_actions:      int
    completed_actions:  int
    completed_weight:   float           = 0.0
    volume_score:       Optional[float] = None


class CumulativeScoreResponse(BaseModel):
    name:           str
    score:          float
    meeting_count:  int
    included_count: int
    excluded_count: int


class FinalScoreResponse(BaseModel):
    name:           str
    meeting_score:  float
    task_score:     Optional[float]
    final:          float
    weights_used:   dict
    leader_applied: bool


class FullPipelineResponse(BaseModel):
    name:       str
    meeting:    CumulativeScoreResponse
    task:       TaskScoreResponse
    final:      FinalScoreResponse
# Author: Garam Mo
# Last Modified: 2026/06/04 by Garam Mo
#
# 역할: Pydantic 스키마 → 엔진 dataclass 변환 헬퍼
# 목적: 라우터 코드에서 반복되는 변환 로직을 한 곳에서 관리

from api.schemas import (
    ActionItemSchema, MemberMeetingDataSchema, TeamSettingsSchema,
)
from engine.models import ActionItem, MemberMeetingData, TeamSettings


def to_action_item(s: ActionItemSchema) -> ActionItem:
    """
    함수명: to_action_item
    설명: ActionItemSchema → ActionItem 변환
    입력:
     - s (ActionItemSchema): Pydantic 스키마
    출력:
     - (ActionItem): 엔진 dataclass
    """
    return ActionItem(
        completed   = s.completed,
        days_late   = s.days_late,
        difficulty  = s.difficulty,
        assigned_at = s.assigned_at,
    )


def to_member_data(s: MemberMeetingDataSchema) -> MemberMeetingData:
    """
    함수명: to_member_data
    설명: MemberMeetingDataSchema → MemberMeetingData 변환
    입력:
     - s (MemberMeetingDataSchema): Pydantic 스키마
    출력:
     - (MemberMeetingData): 엔진 dataclass
    """
    return MemberMeetingData(
        name               = s.name,
        meeting_id         = s.meeting_id,
        meeting_total_sec  = s.meeting_total_sec,
        actual_attend_sec  = s.actual_attend_sec,
        late_sec           = s.late_sec,
        own_chars          = s.own_chars,
        utterance_count    = s.utterance_count,
        total_chars_during = s.total_chars_during,
        team_size          = s.team_size,
        audio_loss_pct     = s.audio_loss_pct,
        speech_confidence  = s.speech_confidence,
        excused_absence    = s.excused_absence,
        excused_late       = s.excused_late,
        absent             = s.absent,
        is_official        = s.is_official,
        is_leader          = s.is_leader,
        actions            = [to_action_item(a) for a in s.actions],
    )


def to_team_settings(s: TeamSettingsSchema) -> TeamSettings:
    """
    함수명: to_team_settings
    설명: TeamSettingsSchema → TeamSettings 변환
    입력:
     - s (TeamSettingsSchema): Pydantic 스키마
    출력:
     - (TeamSettings): 엔진 dataclass
    """
    return TeamSettings(
        weight_speech_in_meeting = s.weight_speech_in_meeting,
        weight_attend_in_meeting = s.weight_attend_in_meeting,
        weight_task_in_final     = s.weight_task_in_final,
        weight_volume_in_task    = s.weight_volume_in_task,
        min_attend_ratio         = s.min_attend_ratio,
        punctuality_grace_ratio  = s.punctuality_grace_ratio,
        late_threshold_sec       = s.late_threshold_sec,
        late_max_sec             = s.late_max_sec,
        absence_grace_sec        = s.absence_grace_sec,
        leader_bonus             = s.leader_bonus,
        action_chars_limit       = s.action_chars_limit,
        deadline_mode            = s.deadline_mode,
        min_meeting_sec          = s.min_meeting_sec,
        score_visibility         = s.score_visibility,
    )

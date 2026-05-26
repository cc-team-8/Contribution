# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 측정 조건에 따른 신뢰도 등급(High/Medium/Low) 산정
# 목적: 데이터 품질을 점수와 함께 제공해 결과 해석의 신뢰성을 높임

from engine.models import MemberMeetingData, ReliabilityLabel


def get_reliability(
    data:          MemberMeetingData,
    measured_axes: int,
) -> ReliabilityLabel:
    """
    함수명: get_reliability
    설명: 측정 조건에 따라 신뢰도 등급을 반환한다.
    입력:
     - data          (MemberMeetingData): 팀원의 회의 데이터
     - measured_axes (int):               실제 측정된 축 수 (0~3)
    출력:
     - (ReliabilityLabel): 신뢰도 등급 (High / Medium / Low)
    """
    meeting_min = data.meeting_total_sec / 60.0
    loss        = data.audio_loss_pct

    # LOW 조건 우선 확인 (하나라도 해당하면 LOW)
    if measured_axes <= 1 or meeting_min < 15 or loss >= 20:
        return ReliabilityLabel.LOW

    # HIGH 조건: 3축 모두 + 30분 이상 + 손실 5% 미만
    if measured_axes == 3 and meeting_min >= 30 and loss < 5:
        return ReliabilityLabel.HIGH

    # 위 두 조건 모두 해당 없으면 MEDIUM
    return ReliabilityLabel.MEDIUM

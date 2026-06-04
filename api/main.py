# Author: Garam Mo
# Last Modified: 2026/06/04 by Garam Mo
#
# 역할: FastAPI 앱 진입점 — 기여도 엔진을 HTTP 엔드포인트로 노출
# 목적: NestJS 백엔드에서 기여도 계산이 필요할 때 내부 HTTP 호출

from fastapi import FastAPI
from api.routes import meeting, task, cumulative, final, pipeline

app = FastAPI(
    title="무임하차 기여도 엔진 API",
    description="회의 기여도 산정 엔진 — 4종류 점수 계산 엔드포인트",
    version="0.2.0",
)

app.include_router(meeting.router,    prefix="/meeting",    tags=["회의 기여도"])
app.include_router(task.router,       prefix="/task",       tags=["태스크 기여도"])
app.include_router(cumulative.router, prefix="/cumulative", tags=["회의 종합 기여도"])
app.include_router(final.router,      prefix="/final",      tags=["최종 종합 기여도"])
app.include_router(pipeline.router,   prefix="/pipeline",   tags=["전체 파이프라인"])


@app.get("/health")
def health():
    return {"status": "ok"}

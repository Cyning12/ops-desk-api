"""Ops Desk API router registration."""
from fastapi import APIRouter

from app.ops.admin.sync import router as admin_sync_router
from app.ops.admin.capability import router as admin_capability_router
from app.ops.auth import router as auth_router
from app.ops.chat.router import router as chat_router
from app.ops.chat.ws import router as chat_ws_router
from app.ops.graph import router as graph_router
from app.ops.issues import router as issues_router
from app.ops.lc_evidence_chain.router import router as lc_evidence_router
from app.ops.lg_rag.router import router as lg_rag_router
from app.ops.overview import router as overview_router
from app.ops.pulls import router as pulls_router

router = APIRouter(prefix="/api/ops")

router.include_router(auth_router)
router.include_router(overview_router)
router.include_router(issues_router)
router.include_router(pulls_router)
router.include_router(graph_router)
router.include_router(admin_sync_router)
router.include_router(admin_capability_router)
router.include_router(chat_router)
router.include_router(chat_ws_router)
router.include_router(lc_evidence_router)
router.include_router(lg_rag_router)

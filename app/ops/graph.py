"""Graph snapshot endpoint."""
from fastapi import APIRouter

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_graph() -> dict:
    """Return latest graph snapshot and module × issue matrix."""
    # TODO: query ops_graph_snapshots latest
    return {
        "snapshot": None,
        "module_matrix": None,
    }

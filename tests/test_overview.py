"""Tests for the overview metrics endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo, OpsScanSnapshot, OpsSyncRun
from app.db.session import AsyncSessionLocal
from app.ops.overview import _median_days
from tests.conftest import DB_AVAILABLE


def test_median_days_odd_sample() -> None:
    pairs = [
        (datetime(2026, 7, 1), datetime(2026, 7, 2)),  # 1 day
        (datetime(2026, 7, 1), datetime(2026, 7, 3)),  # 2 days
        (datetime(2026, 7, 1), datetime(2026, 7, 11)),  # 10 days
    ]
    assert _median_days(pairs) == {"median_days": 2.0, "sample_size": 3}


def test_median_days_even_sample_and_invalid_pairs() -> None:
    pairs = [
        (datetime(2026, 7, 1), datetime(2026, 7, 2)),  # 1 day
        (datetime(2026, 7, 1), datetime(2026, 7, 4)),  # 3 days
        (datetime(2026, 7, 1), None),  # skipped
        (None, datetime(2026, 7, 4)),  # skipped
        (datetime(2026, 7, 5), datetime(2026, 7, 1)),  # end < start, skipped
    ]
    assert _median_days(pairs) == {"median_days": 2.0, "sample_size": 2}


def test_median_days_empty() -> None:
    assert _median_days([]) == {"median_days": None, "sample_size": 0}


async def test_overview_requires_auth(client: AsyncClient) -> None:
    """GET /overview without cookie returns 401."""
    response = await client.get("/api/ops/overview")
    assert response.status_code == 401


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_overview_empty_state(
    client: AsyncClient, override_auth_maintainer, clean_sync_data
) -> None:
    """No data: 200 with null medians, zero throughput, zero-filled trend."""
    response = await client.get("/api/ops/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["cycle_time"] == {"median_days": None, "sample_size": 0}
    assert data["review_time"] == {"median_days": None, "sample_size": 0}
    assert data["issue_throughput"]["count"] == 0
    assert data["sync_status"] == "idle"
    assert data["sync_run"] is None
    assert data["scan_snapshot"] is None
    assert len(data["trend"]) == 30
    assert all(t["closed_issues"] == 0 and t["merged_prs"] == 0 for t in data["trend"])


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_overview_with_seeded_data(
    client: AsyncClient, override_auth_maintainer, clean_sync_data
) -> None:
    """Seeded PRs/issues/sync/scan produce correct metrics."""
    now = datetime.utcnow()
    day = timedelta(days=1)

    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="demo", full_name="acme/demo")
        db.add(repo)
        await db.flush()

        # Cycle times 1, 2, 10 days (median 2.0); first reviews 0.5, 1.5 (median 1.0).
        for i, (cycle, review) in enumerate([(1, 0.5), (2, 1.5), (10, None)], start=1):
            created = now - timedelta(days=cycle) - day
            db.add(
                OpsPullRequest(
                    repo_id=repo.id,
                    number=i,
                    title=f"PR {i}",
                    state="merged",
                    created_at=created,
                    updated_at=created,
                    merged_at=now - day,
                    first_review_at=(
                        created + timedelta(days=review) if review is not None else None
                    ),
                )
            )
        # Old merged PR outside the 90-day window: must not affect median.
        old = now - timedelta(days=200)
        db.add(
            OpsPullRequest(
                repo_id=repo.id,
                number=99,
                title="old",
                state="merged",
                created_at=old,
                updated_at=old,
                merged_at=old + day,
            )
        )

        # Two issues closed within 30 days (one today, one 10 days ago),
        # one closed 60 days ago (outside window), one still open.
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=1,
                title="a",
                state="closed",
                created_at=now - 5 * day,
                updated_at=now,
                closed_at=now,
            )
        )
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=2,
                title="b",
                state="closed",
                created_at=now - 20 * day,
                updated_at=now,
                closed_at=now - 10 * day,
            )
        )
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=3,
                title="c",
                state="closed",
                created_at=now - 70 * day,
                updated_at=now,
                closed_at=now - 60 * day,
            )
        )
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=4,
                title="d",
                state="open",
                created_at=now - 3 * day,
                updated_at=now,
            )
        )

        db.add(
            OpsSyncRun(
                repo_id=repo.id,
                sync_type="full",
                status="success",
                started_at=now - day,
                finished_at=now - day + timedelta(minutes=5),
                summary={"issues": 120, "pulls": 45},
            )
        )
        db.add(
            OpsScanSnapshot(
                repo_id=repo.id,
                parsed_summary={"p0_items": [1, 2], "total_open": 15},
                created_at=now - day,
            )
        )
        await db.commit()

    response = await client.get("/api/ops/overview")
    assert response.status_code == 200
    data = response.json()

    assert data["cycle_time"] == {"median_days": 2.0, "sample_size": 3}
    assert data["review_time"] == {"median_days": 1.0, "sample_size": 2}
    assert data["issue_throughput"] == {"count": 2, "period_days": 30}

    assert data["sync_status"] == "success"
    assert data["sync_run"]["records_issue"] == 120
    assert data["sync_run"]["records_pr"] == 45

    assert data["scan_snapshot"]["parsed_summary"]["total_open"] == 15

    trend = {t["date"]: t for t in data["trend"]}
    assert len(data["trend"]) == 30
    today_str = now.date().isoformat()
    yesterday_str = (now - day).date().isoformat()
    ten_days_ago_str = (now - 10 * day).date().isoformat()
    assert trend[today_str]["closed_issues"] == 1
    assert trend[yesterday_str]["merged_prs"] == 3
    assert trend[ten_days_ago_str]["closed_issues"] == 1

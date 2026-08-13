#!/usr/bin/env python3
"""全量幂等 upsert；可选 RSS 采样钩子（构建期峰值门禁）。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _sample_rss_mb(container: str) -> float | None:
    """docker stats 采样；失败返回 None。"""
    try:
        out = subprocess.check_output(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{.MemUsage}}",
                container,
            ],
            text=True,
            timeout=10,
        ).strip()
        # e.g. "1.2GiB / 3.5GiB"
        used = out.split("/")[0].strip()
        if used.endswith("GiB"):
            return float(used[:-3]) * 1024
        if used.endswith("MiB"):
            return float(used[:-3])
        if used.endswith("KiB"):
            return float(used[:-3]) / 1024
    except Exception:
        return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk upsert points into Qdrant")
    parser.add_argument("--url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="ops_knowledge")
    parser.add_argument("--in", dest="infile", required=True)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--wait", action="store_true", default=True)
    parser.add_argument("--rss-sample-sec", type=int, default=0)
    parser.add_argument("--rss-container", default="qdrant")
    parser.add_argument("--rss-peak-limit-mb", type=float, default=3800)
    parser.add_argument("--ef-construct-fallback", type=int, default=64)
    parser.add_argument("--rss-log", default="")
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm

    client = QdrantClient(url=args.url)
    batch: list[qm.PointStruct] = []
    total = 0
    peak_rss: float | None = None
    last_sample = 0.0
    rss_rows: list[dict] = []

    def flush() -> None:
        nonlocal batch, total
        if not batch:
            return
        client.upsert(
            collection_name=args.collection,
            points=batch,
            wait=args.wait,
        )
        total += len(batch)
        batch = []

    path = Path(args.infile)
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            payload = obj.get("payload") or {}
            for forbidden in ("content", "metadata", "images"):
                if forbidden in payload:
                    raise SystemExit(f"forbidden payload field: {forbidden}")
            batch.append(
                qm.PointStruct(
                    id=int(obj["id"]),
                    vector=list(obj["vector"]),
                    payload=payload,
                )
            )
            if len(batch) >= args.batch_size:
                flush()
            now = time.time()
            if args.rss_sample_sec > 0 and now - last_sample >= args.rss_sample_sec:
                last_sample = now
                rss = _sample_rss_mb(args.rss_container)
                if rss is not None:
                    peak_rss = rss if peak_rss is None else max(peak_rss, rss)
                    rss_rows.append({"t": now, "rss_mb": rss})
                    print(f"rss_sample mb={rss:.1f} peak={peak_rss:.1f}")
                    if rss > args.rss_peak_limit_mb:
                        print(
                            f"WARN: RSS {rss:.1f}MB > {args.rss_peak_limit_mb}; "
                            f"stop and rebuild with ef_construct={args.ef_construct_fallback}",
                            file=sys.stderr,
                        )
                        flush()
                        return 3
    flush()
    if args.rss_log:
        Path(args.rss_log).write_text(
            json.dumps(
                {"peak_rss_mb": peak_rss, "samples": rss_rows, "upserted": total},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(f"upserted {total} points into {args.collection} (peak_rss_mb={peak_rss})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

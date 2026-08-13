#!/usr/bin/env python3
"""从现有 Qdrant collection 循环复制向量，合成扩样至目标 N（默认 800000）。

不写 PG；payload 保留 filter 字段并加 synthetic=true / synth_copy。
新 point id：copy_idx * id_stride + 原 id（uint64 安全范围内）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _sample_rss_mb(container: str) -> float | None:
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


def _ensure_collection(client, name: str, template: str, recreate: bool) -> None:
    from qdrant_client.http import models as qm

    exists = False
    try:
        client.get_collection(name)
        exists = True
    except Exception:
        exists = False

    if exists and not recreate:
        print(f"collection {name} already exists; appending/upserting")
        return
    if exists and recreate:
        client.delete_collection(name)

    src = client.get_collection(template)
    params = src.config.params
    vec = params.vectors
    # Named vs unnamed vectors — production uses unnamed VectorParams
    size = vec.size
    distance = vec.distance
    on_disk = bool(getattr(vec, "on_disk", True))
    hnsw = src.config.hnsw_config
    opt = src.config.optimizer_config

    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=size, distance=distance, on_disk=on_disk),
        hnsw_config=qm.HnswConfigDiff(
            m=hnsw.m,
            ef_construct=hnsw.ef_construct,
            on_disk=bool(getattr(hnsw, "on_disk", True)),
        ),
        optimizers_config=qm.OptimizersConfigDiff(
            indexing_threshold=opt.indexing_threshold,
            max_segment_size=opt.max_segment_size,
        ),
        on_disk_payload=True,
    )
    print(f"created {name} from template={template} dim={size}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic expand Qdrant collection")
    parser.add_argument("--url", default="http://127.0.0.1:6333")
    parser.add_argument("--source", default="ops_knowledge")
    parser.add_argument("--target", default="ops_knowledge_scale")
    parser.add_argument("--target-n", type=int, default=800_000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--id-stride", type=int, default=1_000_000)
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--rss-container", default="ops-desk-api-qdrant-1")
    parser.add_argument("--rss-sample-sec", type=float, default=5.0)
    parser.add_argument("--rss-peak-limit-mb", type=float, default=3800.0)
    parser.add_argument("--rss-log", default="reports/qdrant_migrate/expand_rss.json")
    parser.add_argument("--scroll-batch", type=int, default=256)
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm

    client = QdrantClient(url=args.url, timeout=120)
    src_info = client.get_collection(args.source)
    src_n = int(src_info.points_count or 0)
    if src_n <= 0:
        raise SystemExit(f"source {args.source} empty")

    _ensure_collection(client, args.target, args.source, args.recreate)

    # Load all source points into memory in chunks (N≈8.5k 可接受)
    print(f"scrolling source={args.source} n≈{src_n}")
    points: list[tuple[int, list[float], dict]] = []
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=args.source,
            limit=args.scroll_batch,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )
        for r in records:
            pid = int(r.id)
            vec = r.vector
            if isinstance(vec, dict):
                # named vector — take first
                vec = next(iter(vec.values()))
            payload = dict(r.payload or {})
            for forbidden in ("content", "metadata", "images"):
                payload.pop(forbidden, None)
            points.append((pid, list(vec), payload))
        if offset is None:
            break
    print(f"loaded source points={len(points)}")
    if not points:
        raise SystemExit("no points loaded")

    copies_needed = (args.target_n + len(points) - 1) // len(points)
    if copies_needed * args.id_stride + max(p[0] for p in points) >= 2**63:
        raise SystemExit("id scheme overflow; increase id-stride carefully or lower target")

    peak_rss: float | None = None
    steady_rss: float | None = None
    rss_rows: list[dict] = []
    last_sample = 0.0
    upserted = 0
    stopped_reason = ""

    def sample(force: bool = False) -> None:
        nonlocal peak_rss, last_sample
        now = time.time()
        if not force and now - last_sample < args.rss_sample_sec:
            return
        last_sample = now
        rss = _sample_rss_mb(args.rss_container)
        if rss is None:
            return
        peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        rss_rows.append({"t": now, "rss_mb": rss, "upserted": upserted})
        print(f"rss_sample mb={rss:.1f} peak={peak_rss:.1f} upserted={upserted}")

    batch: list[qm.PointStruct] = []

    def flush() -> None:
        nonlocal batch, upserted
        if not batch:
            return
        client.upsert(collection_name=args.target, points=batch, wait=True)
        upserted += len(batch)
        batch = []
        sample()

    t0 = time.time()
    for copy_idx in range(copies_needed):
        for pid, vec, payload in points:
            if upserted + len(batch) >= args.target_n:
                break
            new_id = copy_idx * args.id_stride + pid
            pl = dict(payload)
            if copy_idx > 0:
                pl["synthetic"] = True
                pl["synth_copy"] = copy_idx
            else:
                # 首批保留原 payload；可选标记
                pl.setdefault("synthetic", False)
            batch.append(qm.PointStruct(id=new_id, vector=vec, payload=pl))
            if len(batch) >= args.batch_size:
                flush()
                if peak_rss is not None and peak_rss > args.rss_peak_limit_mb:
                    stopped_reason = (
                        f"RSS peak {peak_rss:.1f}MB > {args.rss_peak_limit_mb}"
                    )
                    break
        if stopped_reason or upserted >= args.target_n:
            break
        if peak_rss is not None and peak_rss > args.rss_peak_limit_mb:
            break

    flush()
    sample(force=True)
    # 稳态：停写后采样几次
    for _ in range(3):
        time.sleep(2)
        sample(force=True)
    steady_rss = rss_rows[-1]["rss_mb"] if rss_rows else None

    info = client.get_collection(args.target)
    final_n = int(info.points_count or 0)
    elapsed = time.time() - t0

    report = {
        "source": args.source,
        "target": args.target,
        "source_n": len(points),
        "target_n_requested": args.target_n,
        "upserted": upserted,
        "final_points_count": final_n,
        "copies_planned": copies_needed,
        "id_stride": args.id_stride,
        "peak_rss_mb": peak_rss,
        "steady_rss_mb": steady_rss,
        "elapsed_sec": round(elapsed, 2),
        "stopped_reason": stopped_reason or None,
        "samples": rss_rows,
    }
    rss_path = Path(args.rss_log)
    rss_path.parent.mkdir(parents=True, exist_ok=True)
    rss_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "samples"}, indent=2))
    print(f"rss_log={rss_path}")
    if stopped_reason:
        return 3
    if final_n < args.target_n:
        print(
            f"WARN: final_n={final_n} < target={args.target_n}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

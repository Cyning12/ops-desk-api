#!/usr/bin/env python3
"""创建 Qdrant collection：Cosine/1024 + on_disk 向量/HNSW + 轻量 payload。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Qdrant collection (on_disk HNSW)")
    parser.add_argument("--url", default="http://127.0.0.1:6333")
    parser.add_argument("--name", default="ops_knowledge")
    parser.add_argument("--dim", type=int, default=1024)
    parser.add_argument("--metric", default="Cosine", choices=["Cosine", "Euclid", "Dot"])
    parser.add_argument("--m", type=int, default=16)
    parser.add_argument("--ef-construct", type=int, default=100)
    parser.add_argument("--on-disk-vectors", action="store_true", default=True)
    parser.add_argument("--no-on-disk-vectors", action="store_false", dest="on_disk_vectors")
    parser.add_argument("--on-disk-hnsw", action="store_true", default=True)
    parser.add_argument("--no-on-disk-hnsw", action="store_false", dest="on_disk_hnsw")
    parser.add_argument("--on-disk-payload", action="store_true", default=True)
    parser.add_argument("--no-on-disk-payload", action="store_false", dest="on_disk_payload")
    parser.add_argument("--indexing-threshold", type=int, default=10000)
    parser.add_argument("--max-segment-size", type=int, default=20000)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm

    client = QdrantClient(url=args.url)
    exists = False
    try:
        client.get_collection(args.name)
        exists = True
    except Exception:
        exists = False

    if exists and not args.recreate:
        print(f"collection {args.name} already exists; use --recreate to drop")
        return 0
    if exists and args.recreate:
        client.delete_collection(args.name)

    distance = getattr(qm.Distance, args.metric.upper())
    client.create_collection(
        collection_name=args.name,
        vectors_config=qm.VectorParams(
            size=args.dim,
            distance=distance,
            on_disk=args.on_disk_vectors,
        ),
        hnsw_config=qm.HnswConfigDiff(
            m=args.m,
            ef_construct=args.ef_construct,
            on_disk=args.on_disk_hnsw,
        ),
        optimizers_config=qm.OptimizersConfigDiff(
            indexing_threshold=args.indexing_threshold,
            max_segment_size=args.max_segment_size,
        ),
        on_disk_payload=args.on_disk_payload,
    )
    print(
        f"created {args.name}: dim={args.dim} metric={args.metric} "
        f"m={args.m} ef_construct={args.ef_construct} "
        f"on_disk_vectors={args.on_disk_vectors} on_disk_hnsw={args.on_disk_hnsw}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

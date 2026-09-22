#!/usr/bin/env python3
"""多副本验证 D1 · 降级 LB（**自研 Python round-robin / cookie-sticky 反向代理**）。

为什么是自研而不是 nginx/haproxy（诚实标注 · SPEC §2 D1 降级形态）：

- 外部 Java 网关 + Eureka 在**外部仓**（ops-desk-api-java-gateway / ops-desk-eureka-server），
  且本仓 FastAPI 无 Eureka 客户端 —— 「Eureka 注册 2 实例」条目**未覆盖待补**，不撒谎。
- SPEC 命名的降级形态是 compose 内置 nginx/haproxy round-robin；实测本机 docker registry
  拉取受限（docker pull nginx/haproxy 均失败 · 2026-09-22），仓内与本机均无 nginx/haproxy
  镜像/二进制 → 再降级为**宿主机 Python LB**。报告中网关形态栏如实写本段。

功能（验证所需最小集 · 不是生产 LB）：

- round-robin 模式：逐请求轮转两 upstream（无亲和对照组）；
- cookie-sticky 模式：按 ops_session cookie 哈希固定 upstream（会话亲和对照组）；
- 响应注入 X-MR-Upstream: <name> 归属头（归属对拍数据源）；
- 支持 SSE 流式透传（/lg-rag/stream 逐块转发，不缓冲整流）。

用法：python multi_replica_lb.py --port 8199 --mode rr --upstream a=127.0.0.1:8101 --upstream b=127.0.0.1:8102
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class _LB:
    def __init__(self, mode: str, upstreams: list[tuple[str, str]]) -> None:
        if not upstreams:
            raise ValueError("至少一个 upstream")
        self.mode = mode
        self.upstreams = upstreams
        self._rr = itertools.cycle(upstreams)
        self._lock = threading.Lock()
        self.hits: dict[str, int] = {name: 0 for name, _ in upstreams}

    def pick(self, cookie_header: str | None) -> tuple[str, str]:
        if self.mode == "cookie":
            token = ""
            for part in (cookie_header or "").split(";"):
                k, _, v = part.strip().partition("=")
                if k == "ops_session":
                    token = v
                    break
            if token:
                idx = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(self.upstreams)
                return self.upstreams[idx]
        with self._lock:
            return next(self._rr)

    def note(self, name: str) -> None:
        with self._lock:
            self.hits[name] = self.hits.get(name, 0) + 1


def _make_handler(lb: _LB):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args) -> None:  # 静默访问日志（驱动自数归属头）
            return

        def _proxy(self) -> None:
            name, base = lb.pick(self.headers.get("Cookie"))
            lb.note(name)
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None
            url = f"http://{base}{self.path}"
            req = urllib.request.Request(url, data=body, method=self.command)
            for k, v in self.headers.items():
                if k.lower() in ("host", "content-length", "connection"):
                    continue
                req.add_header(k, v)
            try:
                upstream = _OPENER.open(req, timeout=120)
                code = upstream.status
            except urllib.error.HTTPError as exc:
                upstream = exc
                code = exc.code
            except OSError as exc:
                self.send_response(502)
                self.send_header("X-MR-Upstream", name)
                self.end_headers()
                self.wfile.write(f"upstream {name} unreachable: {exc!r}".encode())
                return
            with upstream:
                self.send_response(code)
                for k, v in upstream.headers.items():
                    if k.lower() in (
                        "transfer-encoding", "connection", "content-length",
                    ):
                        continue
                    self.send_header(k, v)
                self.send_header("X-MR-Upstream", name)
                self.end_headers()
                # 逐块透传（SSE 不缓冲；连接关闭即流结束）
                while True:
                    chunk = upstream.read(4096)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
            self.close_connection = True

        # BaseHTTPRequestHandler 派发约定就是 do_<METHOD> 命名（非本文件风格问题）
        do_GET = _proxy  # noqa: N815
        do_POST = _proxy  # noqa: N815
        do_PUT = _proxy  # noqa: N815
        do_DELETE = _proxy  # noqa: N815

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--mode", choices=["rr", "cookie"], default="rr")
    parser.add_argument("--upstream", action="append", default=[],
                        help="name=host:port（可重复）")
    args = parser.parse_args()
    upstreams = []
    for item in args.upstream:
        name, _, addr = item.partition("=")
        upstreams.append((name.strip(), addr.strip()))
    lb = _LB(args.mode, upstreams)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), _make_handler(lb))
    print(f"[multi-replica-lb] :{args.port} mode={args.mode} upstreams={upstreams}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print(f"[multi-replica-lb] hits={lb.hits}", flush=True)


if __name__ == "__main__":
    main()

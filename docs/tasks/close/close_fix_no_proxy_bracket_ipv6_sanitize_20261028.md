# CLOSE：fix-no-proxy-bracket-ipv6-sanitize（启动期清洗 NO_PROXY 方括号 IPv6 条目 · httpx InvalidURL ':1]' 根治）

> 关账日期：2026-10-28 · 关账人：00（delegate-only · 维护者 m00416「也一次性修复了，两个task一起验收吧」授权 + m00729「后端签收归档」）
> 体例承 [close_supervisor_replan_error_feedback_20261027.md](close_supervisor_replan_error_feedback_20261027.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_fix_no_proxy_bracket_ipv6_sanitize.md](../done/task_fix_no_proxy_bracket_ipv6_sanitize.md)（已归档 done/） |
| 性质 | bugfix · 00 delegate-only（10 起草 → 30 实现）· 00 本窗零实现码 |
| 由来 | run 0fbebc8e seq19 worker_failed：`InvalidURL("Invalid port: ':1]'")`——进程继承 shell `NO_PROXY=…,[::1]`，httpx 把 `[::1]` 的 `:1]` 截为端口炸；**四次实证**（含小写 `no_proxy` 漏入的第四实证，佐证双写清洗不可省）；钉案先例 close_vector_waterline_local_rerun_20261017 §四.1 |
| PR | [#295](https://github.com/Cyning12/ops-desk-api/pull/295) MERGED · squash `1d26aa7` · CI 4/4 绿 |
| 审查 | 无独立 R 审查（required_invoke_hats=10,30 · bugfix 轨） |
| 闸 | HG-AUDIT-R1 approved（维护者 m00416 · 00 转录，根因补第四实证）· HG-GRAPH-MODULES n/a |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/main.py:43-68` | `_sanitize_no_proxy_env()`：双键循环（:57-68）· `entry[1:-1]` 剥方括号 · 仅变化回写（:67-68 零 diff） |
| `app/main.py:73` | 调用点：`_init_logging()`（:40）后、app import（:75）前——承 N-40-1 行序先例 |
| `tests/test_no_proxy_sanitize.py` | 8 测：脏 env 复现 InvalidURL 钉 + 清洗后 httpx client 构造钉 + 双键/缺键/零 diff 面 |

## 三、验收核验（4 条全 PASS）

| 验收 | 结果 |
|---|---|
| ① monkeypatch 脏 env → 清洗 + client 构造不炸 | PASS（8 测全绿） |
| ② 无方括号 env 逐字节零 diff | PASS（仅变化回写断言） |
| ③ 大小写双键同处理 / 缺键 no-op | PASS |
| ④ ruff 绿 + 全量零新红 | PASS · 28F/1946P/3s = 基线+8 计账闭合 |

**live 补验（同场验收 5 轨）**：故意脏 env（双键带 `[::1]`）重启 uvicorn PID 20024，health 200；进程内自证 import app.main 后双键均被清洗为 `localhost,127.0.0.1,::1`；run 1039c1a9 全程无 InvalidURL（修复前同场景 seq19 必炸）。

## 四、偏差与照登

1. **小写键漏入第四实证**：首次修复期重启仅覆盖大写 NO_PROXY，小写 no_proxy 仍带 `[::1]`（httpx 按 urllib 惯例小写优先）→ 同炸；task 根因补录后 30 双键覆盖。
2. **ps eww 不可作反证**：macOS ps eww 只映 exec 时环境，运行时 os.environ 改写不反映——自证须进程内读 os.environ。
3. **gh pr create graphql EOF**：首试失败重试即过（transient）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| scripts/evals 等不经 app.main 的直 import 路径 | task 非范围已声明，另议 |
| 用户 shell rc / 系统代理源头 | 维护者自理（task 非范围） |

## 六、维护者 checklist

- [x] 验收 4 条 + live 补验核验完毕（维护者 m00729 签收）
- [x] 00 delegate-only 纪律核验（本窗零实现码）
- [x] 闸真值落闸表（维护者授权 00 转录）
- [x] CI 4/4 绿 · PR #295 合并（squash 1d26aa7）
- [x] 归档 done/ · README 登记 · 50 invoke 落盘

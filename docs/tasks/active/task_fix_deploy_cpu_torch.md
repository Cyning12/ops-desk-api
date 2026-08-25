# Task：fix · 生产部署改装 CPU-only torch（根治 deploy 超时）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：fix / 部署构建优化  
> **现象**：deploy-api 连续三败：① SSH Broken pipe（已修 keepalive）② 30min job 超时（已提 60）③ 60min 仍不够——实证 torch 2.13.0 默认 CUDA 版拖入 nvidia-* 轮子（cudnn 366MB 以 674KB/s 爬、还有 cusparselt 170MB 等，合计数 GB）  
> **根因**：生产 2C4G **无 GPU**，却装 CUDA 全家桶；官方 CPU 版 torch 无 nvidia-* 依赖（约 200MB）  
> **修法**：Dockerfile 先从 pytorch CPU index 装 `torch`，再装 requirements（torch 已被满足则 sentence-transformers 不再拉 CUDA 版）  
> **分支**：`fix/deploy-cpu-torch`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `fix-deploy-cpu-torch` |
| **git_branch** | `fix/deploy-cpu-torch` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | Dockerfile 语法审读；合并后 master push 触发的 deploy run 实证（真验收：build 不再下载 nvidia-* 包） |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者报 CI 失败指示处理 + 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（根因三次实证收敛明确；CPU torch 为无 GPU 服务器标准实践） |

---

## 验收标准

- [x] Dockerfile：requirements 安装前先装 CPU-only torch（pytorch cpu index）；注释写明原因（30 执行 2026-08-25）
- [ ] 合并后 deploy run：build 日志无 nvidia-* 包下载，run 成功（留 00 合并后实证）
- [x] 本地 `ruff check` 无关联改动（仅 Dockerfile，无 Python 改动）；graph-compile exit 0（过闸 · 30 自检通过）

## 风险与回退

| 风险 | 应对 |
|---|---|
| download.pytorch.org 从部署机不可达/慢 | +cpu 轮约 200MB，即便 0.7MB/s 也 ~5min；真不可达则回退并改用镜像站方案（另议） |
| 生产镜像 torch 版本漂移（2.13.0+cu→+cpu） | sentence-transformers 只要求 torch>=1.11；CPU 算子集一致，embedder 本地路径行为不变（生产默认走 SiliconFlow API 嵌入，本地 ST 仅 RAG_EMBED_BACKEND=local 时用） |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：CPU-only torch 根治部署超时 |
| 2026-08-25 | 30 执行：Dockerfile 插入 CPU torch 预装步（注释含 0.67MB/s 实证）；Dockerfile.pg-zhparser 排查无 pip/torch 不动；graph-compile exit 0；deploy 实证项留 00 合并后 |
| 2026-08-25 | 实证 run 32827272733：pytorch cpu index 的依赖（sympy 等）链接 files.pythonhosted.org 直连超时（exit 1）。修法（00 直接）：CPU torch 步加 `--extra-index-url tuna` + `--default-timeout=120 --retries 5`（fix/deploy-cpu-torch-index） |

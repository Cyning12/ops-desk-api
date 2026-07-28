# Harness 30 Prompt · gha-deploy-api（api）

> 用法：Open Folder = `ops-desk-api` 根；新会话整段粘贴下方复制区。  
> 前置：SPEC `docs/spec/SPEC-gha-deploy-api_v1.md` 已 accepted；本 task / R1 已落盘。  
> 分支：从最新 `origin/master`（若 PR #17 未合入，先合入或 rebase 含 SPEC/task 的基线）建 `task/gha-deploy-api`。

---

`````text
你是 Harness 30（含 40 自检）。Open Folder = ops-desk-api 仓根。

读：
- docs/tasks/active/task_gha_deploy_api.md
- docs/spec/SPEC-gha-deploy-api_v1.md
- docs/harness/reviews/task_gha_deploy_api_audit_R1_20260728.md
- docs/harness/reviews/spec_gha-deploy-api_audit_R1_20260728.md（C1–C3）
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
- 金样：../ops-desk-web/.github/workflows/deploy-web.yml
- 金样文档：../ops-desk-web/docs/deployment/gha-frontend-deploy.md
- 对照：../ops-desk-workspace/deploy/deploy.sh（--skip-web 实质；本波不 nginx）

纪律：
1. 首输出 GATE_VERIFY；闸已 approved 才改文件。
2. 禁止 master 直推。从最新 origin/master 建 task/gha-deploy-api。
3. 同波必做：
   - 删除 /health 临时 probe；恢复测试断言；归档 task_health_temp_probe → done/
   - 新增 .github/workflows/deploy-api.yml（push→master + workflow_dispatch；timeout≥20）
   - rsync 仅 /opt/ops-desk/api/（排除项对齐 deploy.sh；禁止 web/）
   - 远端：up -d --build api（C1；不重建 db）；不 reload Nginx（C2）；默认不每次 chown（C3）
   - 健康检查 curl 127.0.0.1:8000/health
   - Secrets 门闩风格对齐 web；文档 docs/deployment/gha-api-deploy.md + README 指针
4. invoke_retention_profile=minimal：落盘 30 invoke。
5. 跑 npx @cyning/harness verify --target . --task docs/tasks/active/task_gha_deploy_api.md
6. pytest tests/test_health.py 必绿。
7. commit → push -u → gh pr create。不 force push。不改 app/ops 业务、不改 deploy-web、不写私钥入仓。

完成后：回填自检；汇报 PR URL；列出维护者首次 Secrets/权限验收清单。
`````

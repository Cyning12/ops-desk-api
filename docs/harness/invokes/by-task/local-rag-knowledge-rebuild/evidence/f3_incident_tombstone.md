# F3 incident: --only docs standalone run triggered tombstone reconciliation (ingest.py:291-302)
- First loop: 9 issues steps + 19 pulls steps ALL OK (each ~10s, attempt=1, zero embed failures).
- Final standalone '--only docs' run: seen={19 docs} -> stale=all 2736 issue/pull units in PG -> to_delete=1855+881 deleted from PG (report shows to_delete=1855 for pulls-scoped view; PG chunks dropped to 219 docs-only). Shadow deletes enqueued to Qdrant.
- Root cause: orchestration error (mine), NOT a code defect: ingest() step-4 tombstone reconciliation deletes any PG unit not in the current run's source set. '--only' partial runs are unsafe as final runs.
- Data safety: zero loss of source data (ops_issues/ops_pull_requests untouched); PG chunks are derived data, re-creatable. Docs chunks (219) intact and hash-unchanged.
- Recovery (zero-code): re-run ascending --limit WITHOUT --only (docs always in seen via load_doc_units) -> issues+pulls re-embedded and rewritten; docs skipped as unchanged; final full run yields to_delete=0.
- Lesson recorded for report: step size 75/source/run (~150 units ~465 chunks < n=500 proven API safe zone).

"""会话摘要保真度金样（session-summary-fallback D4 · 热路径零 LLM-as-judge）。"""

from evals.session.fidelity import check_summary_fidelity

__all__ = ["check_summary_fidelity"]

"""LangChain LCEL：evidence + answer（并行于 LangGraph，默认不挂 graph）。"""

from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer, build_chain

__all__ = ["build_chain", "ainvoke_evidence_answer"]

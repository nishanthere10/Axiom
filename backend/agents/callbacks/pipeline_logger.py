"""
Pipeline Logger — LangChain AsyncCallbackHandler for the LangGraph decision pipeline.

Hooks into every node start/end via the callbacks= arg passed to decision_graph.astream().
Produces structured, single-line log entries compatible with python-json-logger / structlog
so you can grep, parse, or ship them to any log aggregator.

Usage in tasks.py:
    from agents.callbacks.pipeline_logger import PipelineLogger
    cb = PipelineLogger(job_id=job_id, session_id=session_id)
    async for chunk in decision_graph.astream(state, config={"callbacks": [cb]}):
        ...

Log levels:
    INFO  — node_start, node_end, llm_end
    DEBUG — llm_start (prompt preview)
    ERROR — node_error, llm_error  (with exc_info)
"""
import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger("atlas.pipeline")

# State keys that carry large payloads — log counts instead of raw data
_LARGE_LIST_KEYS = {
    "evidence", "retrieved_memories", "github_context",
    "scored_memories", "scored_github", "visual_specs", "visuals",
    "queries", "sub_questions", "constraints",
}
_LARGE_STR_KEYS = {
    "summary", "recommendation", "tradeoffs", "alternatives",
    "reasoning", "memory_context",
}
_MAX_STR_PREVIEW = 120  # chars shown for long string fields


def _summarize_state(state: dict) -> dict:
    """
    Reduce a raw state dict to a log-safe summary.
    Large lists  → "[N items]"
    Long strings → first 120 chars + "…"
    Everything else passes through unchanged.
    """
    out = {}
    for k, v in state.items():
        if k in _LARGE_LIST_KEYS:
            out[k] = f"[{len(v)} items]" if isinstance(v, list) else repr(v)[:60]
        elif k in _LARGE_STR_KEYS:
            s = str(v) if v else ""
            out[k] = (s[:_MAX_STR_PREVIEW] + "…") if len(s) > _MAX_STR_PREVIEW else s
        else:
            out[k] = v
    return out


class PipelineLogger(AsyncCallbackHandler):
    """
    Attaches to a compiled LangGraph via config={"callbacks": [PipelineLogger(...)]}.

    Emits one log line per event:
        node_start  — INFO  — node name + summarised input state
        node_end    — INFO  — node name + duration_ms + summarised output
        node_error  — ERROR — node name + duration_ms + error type + message
        llm_start   — DEBUG — model name + prompt preview (200 chars)
        llm_end     — INFO  — model name + prompt/completion/total tokens
        llm_error   — ERROR — model name + error
    """

    def __init__(self, job_id: str, session_id: str) -> None:
        super().__init__()
        self.job_id = job_id
        self.session_id = session_id
        # run_id (str) → {node: str, start: float}
        self._node_timings: Dict[str, Dict] = {}
        # run_id (str) → {model: str}
        self._llm_calls: Dict[str, Dict] = {}

    # ── helpers ───────────────────────────────────────────────────────────

    def _ctx(self, **extra) -> dict:
        """Common context fields prepended to every log record."""
        return {"job_id": self.job_id, "session_id": self.session_id, **extra}

    @staticmethod
    def _node_name(serialized: dict) -> str:
        return (
            serialized.get("name")
            or (serialized.get("id") or ["?"])[-1]
        )

    # ── Chain (graph node) hooks ──────────────────────────────────────────

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        node = self._node_name(serialized)
        key = str(run_id)
        self._node_timings[key] = {"node": node, "start": time.perf_counter()}

        logger.info(
            "node_start",
            extra=self._ctx(
                event="node_start",
                node=node,
                run_id=key,
                parent_run_id=str(parent_run_id),
                inputs=_summarize_state(inputs) if isinstance(inputs, dict) else str(inputs)[:300],
            ),
        )

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        timing = self._node_timings.pop(key, {})
        node = timing.get("node", "?")
        elapsed_ms = int((time.perf_counter() - timing.get("start", time.perf_counter())) * 1000)

        logger.info(
            "node_end",
            extra=self._ctx(
                event="node_end",
                node=node,
                run_id=key,
                parent_run_id=str(parent_run_id),
                duration_ms=elapsed_ms,
                outputs=_summarize_state(outputs) if isinstance(outputs, dict) else str(outputs)[:300],
            ),
        )

    async def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        timing = self._node_timings.pop(key, {})
        node = timing.get("node", "?")
        elapsed_ms = int((time.perf_counter() - timing.get("start", time.perf_counter())) * 1000)

        logger.error(
            "node_error",
            extra=self._ctx(
                event="node_error",
                node=node,
                run_id=key,
                parent_run_id=str(parent_run_id),
                duration_ms=elapsed_ms,
                error_type=type(error).__name__,
                error=str(error)[:500],
            ),
            exc_info=True,
        )

    # ── LLM hooks (token usage per node) ─────────────────────────────────

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        kw = serialized.get("kwargs") or {}
        model = kw.get("model_name") or kw.get("model") or "?"
        self._llm_calls[str(run_id)] = {"model": model}

        first_prompt = prompts[0] if prompts else ""
        preview = (first_prompt[:200] + "…") if len(first_prompt) > 200 else first_prompt

        logger.debug(
            "llm_start",
            extra=self._ctx(
                event="llm_start",
                model=model,
                run_id=str(run_id),
                parent_run_id=str(parent_run_id),
                num_prompts=len(prompts),
                prompt_preview=preview,
            ),
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        call = self._llm_calls.pop(key, {})
        llm_out = getattr(response, "llm_output", None) or {}
        usage = llm_out.get("token_usage") or {}

        logger.info(
            "llm_end",
            extra=self._ctx(
                event="llm_end",
                model=call.get("model", "?"),
                run_id=key,
                parent_run_id=str(parent_run_id),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
        )

    async def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        call = self._llm_calls.pop(str(run_id), {})
        logger.error(
            "llm_error",
            extra=self._ctx(
                event="llm_error",
                model=call.get("model", "?"),
                run_id=str(run_id),
                parent_run_id=str(parent_run_id),
                error_type=type(error).__name__,
                error=str(error)[:500],
            ),
            exc_info=True,
        )

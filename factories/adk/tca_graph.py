"""ADK graph for the Training Coordinator mock demo."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types
from typing_extensions import override

from factories.adk.paths import repo_root
from factories.adk.tca_tools import function_tools_for

WORKFLOW_PROMPTS = (
    repo_root() / "domains" / "org" / "workflows" / "training-coordinator-agent" / "prompts"
)

AGENT_TOOLS: dict[str, list[str]] = {
    "tca_ingest": ["sharepoint_workday_export_reader"],
    "tca_eligibility": [
        "lookup_governance_rules",
        "sharepoint_roster_reader",
        "compute_eligibility",
        "compute_status",
    ],
    "tca_reconcile": [
        "lookup_trainings_plan",
        "find_session_invite",
        "resolve_session_stakeholders",
        "check_facilitator_availability",
    ],
    "tca_draft": [
        "whats_due_all",
        "draft_session_invite",
        "reschedule_session_invite",
        "cancel_session_invite",
        "reassign_facilitator",
        "draft_email",
        "draft_teams_message",
        "poll_facilitator_availability",
    ],
    "tca_review": [],
    "tca_tracker": ["sharepoint_roster_reader", "recommend_tracker_edit"],
}

PIPELINE = ["tca_ingest", "tca_eligibility", "tca_reconcile", "tca_draft", "tca_review"]
DESCRIPTIONS = {
    "tca_ingest": "Reads new-hire facts from the mock SharePoint Workday export.",
    "tca_eligibility": "Applies deterministic tenure and program rules.",
    "tca_reconcile": "Reconciles trainings.md with committed calendar events.",
    "tca_draft": "Prepares outbound drafts that stay pending_confirmation.",
    "tca_review": "Presents the draft packet and waits for coordinator approval.",
    "tca_tracker": "Recommends exact tracker cell edits. Never writes.",
}

REVIEW_EXTRA = """
This is a local mock demo. Tools return fixture data only.

After you present the packet, STOP. Do not call tools. Do not claim anything
was sent. Ask the coordinator to reply approve or reject.
"""

TRACKER_EXTRA = """
The coordinator already approved. Recommend tracker edits only. Never write
to SharePoint or claim an edit was applied.
"""

APPROVE_WORDS = {"approve", "approved", "yes", "lgtm", "ok", "okay"}
REJECT_WORDS = {"reject", "rejected", "deny", "denied", "no"}
GREET_WORDS = {"hi", "hello", "hey", "help", "yo"}


def _user_text(ctx: InvocationContext) -> str:
    content = ctx.user_content
    if content is None or not content.parts:
        return ""
    return " ".join(part.text or "" for part in content.parts).strip()


def _decision(text: str) -> str | None:
    tokens = {t.strip(".,!?") for t in text.lower().split()}
    if tokens & APPROVE_WORDS:
        return "approve"
    if tokens & REJECT_WORDS:
        return "reject"
    return None


class TcaDemoRoot(BaseAgent):
    """Runs ingest→review, then tracker only after a chat approval."""

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        text = _user_text(ctx)
        tokens = {t.strip(".,!?") for t in text.lower().split()}
        if tokens <= GREET_WORDS or text.lower().strip() in GREET_WORDS:
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=(
                                "I am the Field Onboarding coordinator (GM, FOD, OEM Parts). "
                                "Ask what is due for a week, or paste a hire-export question. "
                                "Example: What's due for GM and OEM Parts the week of 2026-09-21?"
                            )
                        )
                    ],
                ),
            )
            return
        decision = _decision(text)
        children = {child.name: child for child in self.sub_agents}
        if decision == "approve":
            async for event in children["tca_tracker"].run_async(ctx):
                yield event
            return
        if decision == "reject":
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=(
                                "Drafts rejected. Nothing was sent or written. "
                                "Start a new query to rebuild the packet."
                            )
                        )
                    ],
                ),
            )
            return
        for name in PIPELINE:
            async for event in children[name].run_async(ctx):
                yield event


def _prompt(name: str) -> str:
    return (WORKFLOW_PROMPTS / f"{name}_1.0.0.md").read_text(encoding="utf-8")


def _make_llm_agent(name: str, model, extra: str = "") -> LlmAgent:
    instruction = _prompt(name)
    if extra:
        instruction = f"{instruction}\n{extra}"
    kwargs: dict = {
        "name": name,
        "model": model,
        "description": DESCRIPTIONS[name],
        "instruction": instruction,
    }
    tools = function_tools_for(AGENT_TOOLS[name])
    if tools:
        kwargs["tools"] = tools
    return LlmAgent(**kwargs)


def _adk_model(model=None):
    if model is not None:
        return model
    if os.getenv("OPENROUTER_API_KEY"):
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(
            model=os.getenv("ADK_DEFAULT_MODEL", "openrouter/openai/gpt-oss-120b"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            # LiteLLM 1.106.0 imports mcp.types.CacheableResult on any tools=
            # call; mcp 1.x does not export it. Skip the proxy MCP gateway.
            _skip_mcp_handler=True,
        )
    return os.getenv("ADK_DEFAULT_MODEL", "gemini-2.5-flash")


def build_root_agent(model=None) -> TcaDemoRoot:
    resolved = _adk_model(model)
    sub_agents = [
        _make_llm_agent(name, resolved, extra=REVIEW_EXTRA if name == "tca_review" else "")
        for name in PIPELINE
    ]
    sub_agents.append(_make_llm_agent("tca_tracker", resolved, extra=TRACKER_EXTRA))
    return TcaDemoRoot(
        name="training_coordinator",
        description=(
            "Mock Training Coordinator: ingest, eligibility, reconcile, "
            "draft, review (HITL), then tracker after approve."
        ),
        sub_agents=sub_agents,
    )


def build_tca_agents(model=None) -> dict[str, LlmAgent]:
    resolved = _adk_model(model)
    agents = {name: _make_llm_agent(name, resolved) for name in PIPELINE}
    agents["tca_tracker"] = _make_llm_agent("tca_tracker", resolved, extra=TRACKER_EXTRA)
    return agents

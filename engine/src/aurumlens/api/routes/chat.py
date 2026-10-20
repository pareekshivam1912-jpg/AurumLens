"""Chatbot API Routes for AurumLens AI.

Exposes unified conversational endpoints backed by deterministic quant tools
and strict NumericGuard verification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aurumlens.explain.chatbot import AurumLensAIChatbot

chat_router = APIRouter(prefix="/v1/chat", tags=["AI Chatbot"])
_bot = AurumLensAIChatbot()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User question or command")
    language: str = Field("en", pattern="^(en|hi)$", description="Preferred response language: 'en' or 'hi'")
    session_id: Optional[str] = Field(None, description="Client session ID for conversation tracking")


class ActionCard(BaseModel):
    type: str
    proposal_id: str
    title: str
    pair_name: str
    summary: str
    notional: float
    margin: float
    friction: float
    residual_fine_g: float


class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: str
    tool_called: Optional[str] = None
    tool_data: Optional[Dict[str, Any]] = None
    action_card: Optional[ActionCard] = None
    passed_numeric_guard: bool
    language: str
    timestamp: str


@chat_router.post("", response_model=ChatResponse)
def handle_chat_message(req: ChatRequest) -> ChatResponse:
    """Send a message to AurumLens AI and receive an audited, tool-grounded response."""
    res = _bot.process_message(
        query=req.message,
        language=req.language,
        session_id=req.session_id,
    )
    return ChatResponse(**res)


@chat_router.get("/suggestions")
def get_prompt_suggestions() -> List[Dict[str, str]]:
    """Return quick starter chips for the conversational assistant."""
    return [
        {
            "id": "diag",
            "label": "Why was GOLDTEN-GOLDGUINEA blocked on Oct 1st?",
            "category": "Diagnostics",
        },
        {
            "id": "portfolio",
            "label": "Check my paper portfolio & margin status",
            "category": "Portfolio",
        },
        {
            "id": "stress",
            "label": "What happens if gold drops 5%?",
            "category": "Risk Stress",
        },
        {
            "id": "stage",
            "label": "Stage a paper trade on GOLDTEN-GOLDGUINEA",
            "category": "Trading",
        },
        {
            "id": "purity",
            "label": "How does GOLDM 995 purity normalization work?",
            "category": "Guide",
        },
    ]

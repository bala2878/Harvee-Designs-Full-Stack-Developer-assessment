import json
import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools import TOOL_DEFINITIONS, TOOL_IMPLEMENTATIONS
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an analytics assistant for a university course allocation system.
Answer the user's question ONLY using data returned by the tools available to you — never invent
numbers. Always call the relevant tool(s) before answering. If a question needs multiple tools
(e.g. comparing two things), call all of them before composing your final answer.
Keep answers concise, use concrete numbers from tool results, and format lists/tables in markdown
when that improves readability. If the tools return no data, say so plainly instead of guessing."""

MAX_TOOL_ROUNDS = 4


class AIAssistantError(Exception):
    pass


async def ask_assistant(db: AsyncSession, question: str) -> dict:
    """Runs the tool-use loop and returns {"answer": str, "tool_calls": [...]}."""
    if not settings.OPENAI_API_KEY:
        raise AIAssistantError(
            "OPENAI_API_KEY is not configured. Set it in the environment to enable the AI assistant."
        )

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key="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")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_call_log = []

    for _round in range(MAX_TOOL_ROUNDS):
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls

        if not tool_calls:
            return {"answer": (message.content or "").strip(), "tool_calls": tool_call_log}

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ],
            }
        )

        for tc in tool_calls:
            fn = TOOL_IMPLEMENTATIONS.get(tc.function.name)
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {}

            if fn is None:
                result_payload = {"error": f"unknown tool {tc.function.name}"}
            else:
                try:
                    result_payload = await fn(db, **args)
                except Exception as exc:
                    logger.exception("AI tool execution failed: %s", tc.function.name)
                    result_payload = {"error": str(exc)}

            tool_call_log.append({"tool": tc.function.name, "input": args, "result": result_payload})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result_payload, default=str),
                }
            )

    raise AIAssistantError("AI assistant exceeded maximum tool-use rounds without producing a final answer.")
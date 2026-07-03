"""
Thin async-friendly wrapper around Amazon Bedrock's Converse API.

We use boto3's `bedrock-runtime` client (synchronous) inside a thread pool
executor so the rest of the codebase can `await` it like any other async
dependency. The Converse API is model-agnostic across Bedrock-hosted models,
which keeps this wrapper stable if the underlying model id changes.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BedrockClient:
    """Wraps Bedrock Converse for both plain chat completion and
    tool-calling (function-calling) style agent steps."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
        )
        self.model_id = settings.bedrock_model_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _converse_sync(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens or settings.bedrock_max_tokens,
                "temperature": temperature if temperature is not None else settings.bedrock_temperature,
            },
        }
        if system:
            kwargs["system"] = [{"text": system}]
        if tools:
            kwargs["toolConfig"] = {"tools": tools}

        return self._client.converse(**kwargs)

    async def converse(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self._converse_sync(messages, system, tools, max_tokens, temperature),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("bedrock.converse_failed", error=str(exc))
            raise

        return response

    @staticmethod
    def extract_text(response: Dict[str, Any]) -> str:
        """Pulls plain text out of a Converse API response."""
        try:
            content_blocks = response["output"]["message"]["content"]
            texts = [block["text"] for block in content_blocks if "text" in block]
            return "\n".join(texts).strip()
        except (KeyError, IndexError):
            return ""

    @staticmethod
    def extract_tool_use(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Returns the first tool-use block, if the model invoked a tool."""
        try:
            content_blocks = response["output"]["message"]["content"]
            for block in content_blocks:
                if "toolUse" in block:
                    return block["toolUse"]
        except (KeyError, IndexError):
            pass
        return None

    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Asks the model to respond with strict JSON and parses it,
        recovering from accidental markdown code fences."""
        json_system = (
            (system or "")
            + "\nRespond with ONLY valid, minified JSON. No markdown, no commentary, no code fences."
        )
        response = await self.converse(
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            system=json_system,
            max_tokens=max_tokens,
        )
        text = self.extract_text(response)
        cleaned = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("bedrock.json_parse_failed", raw=text[:500])
            return {"_raw": text, "_parse_error": True}


_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client

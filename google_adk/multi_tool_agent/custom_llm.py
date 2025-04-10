import asyncio
from typing import AsyncGenerator
import aiohttp

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
import random

class MyLlm(BaseLlm):
    @classmethod
    def supported_models(cls) -> list[str]:
        return [r"my-llm.*"]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        prompt = self._build_prompt_from_contents(llm_request.contents)

        temperature = llm_request.config.temperature if llm_request.config else 0.7
        max_tokens = llm_request.config.max_output_tokens if llm_request.config else 512

        try:
            text = await self._call_my_model(prompt, temperature, max_tokens)

            content = types.Content(
                role="model",  # Optional, could also be "assistant"
                parts=[types.Part(text=text)]
            )

            yield LlmResponse(
                content=content,
                partial=False,
                turn_complete=True
            )

        except Exception as e:
            yield LlmResponse(
                error_code="LLM_BACKEND_ERROR",
                error_message=str(e)
            )

    def _build_prompt_from_contents(self, contents: list[types.Content]) -> str:
        prompt_lines = []
        for content in contents:
            role = content.role or "user"
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    prompt_lines.append(f"{role}: {part.text}")
        return "\n".join(prompt_lines)

    async def _call_my_model(self, prompt: str, temperature: float, max_tokens: int) -> str:
        await asyncio.sleep(0.2)  # simulate network delay
        responses = [
            "Sure, here's a detailed explanation.",
            "That's a great question — let me help.",
            "Hello from your custom LLM!",
            "The quick brown fox jumps over the lazy dog.",
            "42 is the answer to life, the universe, and everything."
        ]
        return random.choice(responses)

    async def _call_my_model1(self, prompt: str, temperature: float, max_tokens: int) -> str:
        url = "http://localhost:8000/generate"
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("text", "")

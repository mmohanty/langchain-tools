# my_llm.py

import asyncio
from typing import AsyncGenerator
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

class MyLlm(BaseLlm):
    @classmethod
    def supported_models(cls) -> list[str]:
        return [r"my-llm.*"]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        prompt = llm_request.prompt
        # Replace with your actual LLM call here (local or API)
        response_text = await self._call_my_model(prompt)

        # Yield response in LlmResponse format
        yield LlmResponse(text=response_text)

    async def _call_my_model(self, prompt: str) -> str:
        # Simulated async call to your LLM
        await asyncio.sleep(0.2)
        return f"[MyLLM response to]: {prompt}"

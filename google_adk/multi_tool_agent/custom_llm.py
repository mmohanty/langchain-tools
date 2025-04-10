import asyncio
from typing import AsyncGenerator
import aiohttp

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.genai import types
import random

from google.genai.types import Content, Part, FunctionCall
from google.adk.models.llm_response import LlmResponse
from langchain.schema import HumanMessage, SystemMessage, AIMessage, FunctionMessage
from langchain.tools.render import format_tool_to_openai_function
from langchain.chat_models import ChatOpenAI




class MyLlm(BaseLlm):
    @classmethod
    def supported_models(cls) -> list[str]:
        return [r"my-llm.*"]

    async def generate_content_async1(
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

    def _format_chat_history(self, contents: list[types.Content]) -> list[dict]:
        messages = []
        for content in contents:
            role = content.role or "user"
            for part in content.parts:
                if hasattr(part, "text"):
                    messages.append({
                        "role": role,
                        "content": part.text
                    })
        return messages


    def _format_tool_schemas(self, tools: list[types.Tool]) -> list[dict]:
        tool_list = []
        for tool in tools:
            for func in tool.function_declarations:
                tool_list.append({
                    "name": func.name,
                    "description": func.description,
                    "parameters": func.parameters.model_dump()  # pydantic model to dict
                })
        return tool_list


    async def generate_content_async(
            self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        # 1. Extract system/user content
        messages = self._format_chat_history(llm_request.contents)

        # 2. Extract tools from config
        tool_schemas = self._format_tool_schemas(llm_request.config.tools)
        print(tool_schemas)

        # 3. Build final prompt
        prompt = {
            "messages": messages,
            "tools": tool_schemas,
            "tool_choice": "auto",
            "temperature": llm_request.config.temperature if llm_request.config else 0.7,
            "max_tokens": llm_request.config.max_output_tokens if llm_request.config else 512,
        }

        # 4. Call backend LLM
        # response = await self._call_my_llm_api(prompt)
        #
        #
        # if "tool_call" in response:
        #     tool_call_part = Part(
        #         function_call=FunctionCall(
        #             name="get_weather",
        #             args={"city": "New York"}
        #         )
        #     )
        #     content = Content(role="model", parts=[tool_call_part])
        #
        #     yield LlmResponse(
        #         content=content,
        #         partial=False,
        #         turn_complete=True
        #     )
        # else:
        #     content = types.Content(role="model", parts=[types.Part(text=response["text"])])
        #     yield LlmResponse(content=content, partial=False, turn_complete=True)

        # 4. Call backend LLM - OpenaAI Standard
        response = await self._call_my_llm_api(llm_request)

        if "tool_call" in response:
            yield LlmResponse(
                content=Content(
                    role="model",
                    parts=[
                        Part(
                            function_call=FunctionCall(
                                name=response["tool_call"]["name"],
                                args=response["tool_call"]["args"]
                            )
                        )
                    ]
                )
            )
        else:
            yield LlmResponse(
                content=Content(
                    role="model",
                    parts=[Part(text=response["text"])]
                ),
                partial=False,
                turn_complete=True
            )

    async def _call_my_llm_api_dummy(self, prompt: dict) -> dict:
        # Simulate a tool trigger when "weather" is in the prompt
        full_text = " ".join(m["content"] for m in prompt["messages"])

        if "weather" in full_text.lower():
            return {
                "tool_call": {
                    "name": "get_weather",
                    "args": {"city": "New York"}
                }
            }

        return {"text": "Sorry, I don't understand the question."}


    def _convert_adk_tools_to_openai_format(self, tools: list[types.Tool]):
        return [
            format_tool_to_openai_function(tool.function_declarations[0])
            for tool in tools
        ]


    def _convert_to_langchain_messages(self, contents: list[types.Content]):
        messages = []
        for content in contents:
            role = content.role or "user"
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    if role == "system":
                        messages.append(SystemMessage(content=part.text))
                    elif role == "user":
                        messages.append(HumanMessage(content=part.text))
                    elif role == "model":
                        messages.append(AIMessage(content=part.text))
                    elif role == "function":
                        messages.append(FunctionMessage(content=part.text, name="tool_name"))
        return messages

    async def _call_my_llm_api_openai_standard(self, llm_request: LlmRequest) -> dict:
        messages = self._convert_to_langchain_messages(llm_request.contents)
        functions = self._convert_adk_tools_to_openai_format(llm_request.config.tools)

        llm = ChatOpenAI(
            model="gpt-4-0613",  # or gpt-3.5-turbo-0613
            temperature=0.7,
            openai_api_key="YOUR_KEY",  # or from env
        )

        response = await llm.ainvoke(
            messages,
            functions=functions,
            function_call="auto"  # let model decide
        )

        if response.additional_kwargs.get("function_call"):
            fn_call = response.additional_kwargs["function_call"]
            return {
                "tool_call": {
                    "name": fn_call["name"],
                    "args": fn_call["arguments"]
                }
            }

        return {"text": response.content}
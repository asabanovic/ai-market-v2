"""LLM utilities for agents."""

import os
from typing import List
from openai import OpenAI


_openai_client = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _openai_client


def get_embedding_model(model: str = "text-embedding-3-small"):
    """Get embedding function."""
    client = get_openai_client()

    def embed(text: str) -> List[float]:
        response = client.embeddings.create(model=model, input=text)
        return response.data[0].embedding

    return embed


async def get_chat_model(model: str = "gpt-4o-mini", temperature: float = 0.3):
    """Get chat model function."""
    client = get_openai_client()

    async def chat(messages: List[dict], **kwargs) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )
        return response.choices[0].message.content

    return chat

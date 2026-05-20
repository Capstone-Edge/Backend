import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AI_MCP_BASE_URL = os.getenv("AI_MCP_BASE_URL", "http://127.0.0.1:8001")


async def request_parse_to_ai_mcp(payload: dict):
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{AI_MCP_BASE_URL}/parse",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
async def request_clarify_to_ai_mcp(payload: dict):
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{AI_MCP_BASE_URL}/clarify",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
async def request_clarify_and_execute_to_ai_mcp(payload: dict):
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{AI_MCP_BASE_URL}/clarify-and-execute",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
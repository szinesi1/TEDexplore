"""
Client Ollama + TEDexplore MCP.
Collega un modello Ollama locale al server MCP di TEDexplore, lasciando
che sia l'LLM a decidere quando chiamare i tool (es. get_watch_next).
Homework 3 - unibg_tedx_2026
"""

import asyncio

import ollama
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# ============================================================
# CONFIG
# ============================================================

SERVER_URL = "http://127.0.0.1:8443/mcp"
OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# HELPERS
# ============================================================

def mcp_tools_to_ollama(mcp_tools):
    """Converte la lista di tool MCP nel formato richiesto da Ollama."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        }
        for t in mcp_tools
    ]


async def chat(session: ClientSession, user_message: str):

    mcp_tools = (await session.list_tools()).tools
    ollama_tools = mcp_tools_to_ollama(mcp_tools)

    messages = [{"role": "user", "content": user_message}]

    print(f"\n{'=' * 60}")
    print(f"Domanda: {user_message}")
    print("=" * 60)

    # Ciclo: chiedi a Ollama, esegui eventuali tool richiesti, ripeti
    for _ in range(5):

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=ollama_tools,
        )

        msg = response["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            print(f"\n🤖 {msg['content']}")
            return

        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            print(f"\n🔧 Chiamata tool MCP: {name}({args})")

            result = await session.call_tool(name, arguments=args)
            text = "\n".join(
                c.text for c in result.content if hasattr(c, "text")
            )

            print(f"   → risultato: {text[:300]}{'...' if len(text) > 300 else ''}")

            messages.append({"role": "tool", "content": text, "name": name})

    print("⚠️  Raggiunto il numero massimo di iterazioni.")


# ============================================================
# MAIN
# ============================================================

async def main():

    print(f"Connessione a {SERVER_URL}...")

    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:

            await session.initialize()
            print(f"✓ Connesso. Modello Ollama in uso: {OLLAMA_MODEL}\n")

            tools = await session.list_tools()
            print("Tool disponibili sul server:")
            for t in tools.tools:
                print(f"  • {t.name} — {t.description}")

            # Domande di prova per la demo / screenshot
            await chat(session, "Ho appena finito un talk con video_id 7459, cosa mi consigli di guardare dopo?")
            await chat(session, "Trovami dei talk TEDx sul tema 'technology'.")


if __name__ == "__main__":
    asyncio.run(main())

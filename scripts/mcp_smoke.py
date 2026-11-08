import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def schema_of(tool):
    return getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None) or {}


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_mcp.py <server command and args>")
        sys.exit(2)
    command, *args = sys.argv[1:]
    params = StdioServerParameters(command=command, args=args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            if not tools:
                print("FAIL: server exposes no tools")
                sys.exit(1)
            for t in tools:
                props = schema_of(t).get("properties", {})
                print("TOOL:", t.name)
                print("  inputs:", json.dumps(props)[:200])
            print(f"OK: {len(tools)} tool(s) found")

            domain = os.environ.get("TEST_DOMAIN")
            if domain:
                tool = tools[0]
                schema = schema_of(tool)
                required = schema.get("required") or list(schema.get("properties", {}))
                key = required[0] if required else "domain"
                print(f"CALL: {tool.name}({key}={domain})")
                try:
                    result = await session.call_tool(tool.name, {key: domain})
                    failed = getattr(result, "is_error", None) or getattr(result, "isError", False)
                    text = "".join(getattr(c, "text", "") for c in result.content)
                    print("FAIL:" if failed else "RESULT OK:", text[:400])
                except Exception as e:
                    print("FAIL:", type(e).__name__, e)
                    sys.exit(1)


asyncio.run(main())

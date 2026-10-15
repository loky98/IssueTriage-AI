import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            res = await session.call_tool("search_github_issues", {"query": "read_csv separator"})
            print(res.content[0].text[:500])
            res = await session.call_tool("run_snippet", {"code": "import pandas as pd; print(pd.__version__)"})
            print(res.content[0].text)


asyncio.run(main())
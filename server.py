"""
Dev Assistant MCP Server
A multi-tool MCP server for engineering workflows:
  - Log analysis & error summarization
  - Code review & suggestions
  - GitHub issues fetching & summarization
"""

from fastmcp import FastMCP
from tools.log_analyzer import analyze_logs
from tools.code_reviewer import review_code
from tools.github_issues import fetch_github_issues

mcp = FastMCP(
    name="Dev Assistant",
    instructions=(
        "A developer productivity assistant with three tools: "
        "analyze_logs for diagnosing errors in log output, "
        "review_code for reviewing code and suggesting improvements, "
        "and fetch_github_issues for summarizing open GitHub issues."
    ),
)

mcp.tool(analyze_logs)
mcp.tool(review_code)
mcp.tool(fetch_github_issues)

if __name__ == "__main__":
    mcp.run(transport="stdio")

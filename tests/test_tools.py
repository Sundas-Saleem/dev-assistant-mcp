"""
Tests for Dev Assistant MCP tools.
Run with: pytest tests/ -v
"""

import pytest
from tools.log_analyzer import analyze_logs
from tools.code_reviewer import review_code
from tools.github_issues import fetch_github_issues


# ─── Log Analyzer ──────────────────────────────────────────────────────────────

class TestLogAnalyzer:
    def test_detects_errors(self):
        logs = """
2024-01-01 10:00:00 INFO Starting service
2024-01-01 10:00:01 ERROR Database connection failed
2024-01-01 10:00:02 ERROR Database connection failed
2024-01-01 10:00:03 WARNING Retrying connection
        """
        result = analyze_logs(logs)
        assert result["summary"]["total_errors"] == 2
        assert result["summary"]["total_warnings"] == 1
        assert result["top_errors"][0]["occurrences"] >= 1

    def test_detects_stack_traces(self):
        logs = """
Traceback (most recent call last):
  File "app.py", line 42, in handle_request
    result = db.query(sql)
ConnectionError: Lost connection to database
        """
        result = analyze_logs(logs)
        assert result["summary"]["stack_traces_found"] >= 1

    def test_clean_logs(self):
        logs = """
2024-01-01 10:00:00 INFO Service started
2024-01-01 10:00:01 INFO Request processed
        """
        result = analyze_logs(logs)
        assert result["summary"]["total_errors"] == 0
        assert "No errors" in result["diagnosis"]

    def test_empty_logs(self):
        result = analyze_logs("")
        assert result["summary"]["total_lines"] == 0


# ─── Code Reviewer ─────────────────────────────────────────────────────────────

class TestCodeReviewer:
    def test_detects_bare_except(self):
        code = """
def fetch():
    try:
        return requests.get(url)
    except:
        pass
        """
        result = review_code(code, language="python")
        issues = [i["issue"] for i in result["issues"]]
        assert any("bare except" in i.lower() for i in issues)

    def test_detects_hardcoded_secret(self):
        code = 'api_key = "sk-abc123def456ghi789"'
        result = review_code(code, language="python")
        high_issues = [i for i in result["issues"] if i["severity"] == "high"]
        assert len(high_issues) >= 1

    def test_detects_print_statements(self):
        code = """
def process(data):
    print(data)
    return data
        """
        result = review_code(code, language="python")
        issues = [i["issue"] for i in result["issues"]]
        assert any("print" in i.lower() for i in issues)

    def test_clean_code(self):
        code = """
import logging

logger = logging.getLogger(__name__)

def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
        """
        result = review_code(code, language="python")
        assert result["issues_found"] == 0

    def test_language_detection(self):
        code = "public class Main { public static void main(String[] args) {} }"
        result = review_code(code)
        assert result["language_detected"] == "java"

    def test_empty_code(self):
        result = review_code("")
        assert "error" in result


# ─── GitHub Issues ──────────────────────────────────────────────────────────────

class TestGitHubIssues:
    def test_invalid_repo_format(self):
        result = fetch_github_issues("notarepo")
        assert "error" in result

    def test_nonexistent_repo(self):
        result = fetch_github_issues("nonexistent-owner-xyz/nonexistent-repo-xyz")
        assert "error" in result

    def test_valid_public_repo(self):
        result = fetch_github_issues("psf/requests", max_issues=5)
        # Either returns issues or a rate-limit/network error — both are valid responses
        if "error" in result:
            assert isinstance(result["error"], str)  # graceful error message
        else:
            assert "total_fetched" in result
            assert isinstance(result["issues"], list)

    def test_analytics_structure(self):
        result = fetch_github_issues("psf/requests", max_issues=5)
        if "error" not in result and result["total_fetched"] > 0:
            assert "top_labels" in result["analytics"]
            assert "avg_comments" in result["analytics"]

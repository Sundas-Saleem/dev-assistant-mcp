"""
GitHub Issues Tool
Fetches open issues from a public GitHub repository and returns a structured summary.
"""

import urllib.request
import urllib.error
import json
from typing import Optional
from collections import Counter


def fetch_github_issues(
    repo: str,
    state: Optional[str] = "open",
    max_issues: Optional[int] = 20,
    label: Optional[str] = None,
) -> dict:
    """
    Fetch and summarize issues from a public GitHub repository.

    Args:
        repo: GitHub repository in 'owner/repo' format (e.g. 'psf/requests').
        state: Issue state — 'open', 'closed', or 'all'. Default is 'open'.
        max_issues: Maximum number of issues to fetch (default 20, max 100).
        label: Optional label to filter by (e.g. 'bug', 'enhancement').

    Returns:
        Structured summary with issue list, label breakdown, and top contributors.
    """
    if "/" not in repo:
        return {"error": "Invalid repo format. Use 'owner/repo' (e.g. 'psf/requests')."}

    max_issues = min(max_issues or 20, 100)
    state = state or "open"

    # Build URL
    url = f"https://api.github.com/repos/{repo}/issues?state={state}&per_page={max_issues}"
    if label:
        url += f"&labels={label}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "dev-assistant-mcp/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"Repository '{repo}' not found or is private."}
        return {"error": f"GitHub API error: HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}

    # Filter out pull requests (GitHub API returns PRs in issues endpoint)
    issues = [item for item in raw if "pull_request" not in item]

    if not issues:
        return {
            "repo": repo,
            "state": state,
            "total_fetched": 0,
            "issues": [],
            "summary": f"No {state} issues found in {repo}.",
        }

    # Parse issues
    parsed = []
    all_labels = []
    authors = []

    for issue in issues:
        labels = [lbl["name"] for lbl in issue.get("labels", [])]
        all_labels.extend(labels)
        author = issue.get("user", {}).get("login", "unknown")
        authors.append(author)

        parsed.append({
            "number": issue["number"],
            "title": issue["title"],
            "author": author,
            "state": issue["state"],
            "labels": labels,
            "comments": issue.get("comments", 0),
            "created_at": issue["created_at"][:10],
            "url": issue["html_url"],
        })

    # Analytics
    label_counts = Counter(all_labels).most_common(10)
    author_counts = Counter(authors).most_common(5)
    high_activity = [i for i in parsed if i["comments"] >= 5]

    return {
        "repo": repo,
        "state": state,
        "label_filter": label or "none",
        "total_fetched": len(parsed),
        "issues": parsed,
        "analytics": {
            "top_labels": [{"label": l, "count": c} for l, c in label_counts],
            "top_authors": [{"author": a, "issues": c} for a, c in author_counts],
            "high_activity_issues": len(high_activity),
            "avg_comments": round(sum(i["comments"] for i in parsed) / len(parsed), 1),
        },
        "summary": (
            f"Fetched {len(parsed)} {state} issue(s) from {repo}. "
            + (f"Top label: '{label_counts[0][0]}'. " if label_counts else "")
            + (f"{len(high_activity)} issue(s) with 5+ comments (high activity)." if high_activity else "")
        ),
    }

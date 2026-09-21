"""
Code Reviewer Tool
Analyzes code for issues, anti-patterns, and improvement opportunities.
"""

import re
from typing import Optional


# Common patterns to flag per language
PYTHON_PATTERNS = [
    (r"except\s*:", "Bare except clause — catches all exceptions including SystemExit. Specify exception type."),
    (r"print\s*\(", "print() found — use logging module for production code."),
    (r"TODO|FIXME|HACK|XXX", "Unresolved TODO/FIXME comment found."),
    (r"import \*", "Wildcard import — makes namespace unclear. Import explicitly."),
    (r"eval\s*\(", "eval() is a security risk — avoid in production code."),
    (r"time\.sleep\s*\(", "time.sleep() in code — consider async alternatives if in async context."),
    (r"password|secret|api_key\s*=\s*['\"]", "Potential hardcoded credential detected."),
    (r"global\s+\w+", "Global variable usage — prefer passing state explicitly."),
    (r"assert\s+", "assert statement — disabled in optimized mode (-O). Use explicit checks instead."),
]

JAVA_PATTERNS = [
    (r"catch\s*\(\s*Exception\s+", "Catching generic Exception — catch specific exceptions instead."),
    (r"System\.out\.print", "System.out.println found — use a logging framework (SLF4J, Log4j)."),
    (r"TODO|FIXME|HACK", "Unresolved TODO/FIXME comment found."),
    (r"new\s+\w+\(\)", "Object instantiation — consider dependency injection or factory pattern."),
    (r"password|secret|apiKey\s*=\s*\"", "Potential hardcoded credential detected."),
    (r"\.equals\s*\(null\)", "Use == null instead of .equals(null) to avoid NullPointerException."),
    (r"Thread\.sleep\s*\(", "Thread.sleep() found — may indicate blocking in async context."),
]

GENERIC_PATTERNS = [
    (r"password|secret|api_key|apikey|token\s*=\s*['\"][\w\-]{6,}", "Potential hardcoded secret detected."),
    (r"TODO|FIXME|HACK|XXX", "Unresolved TODO/FIXME found."),
    (r"http://", "HTTP (non-HTTPS) URL detected — use HTTPS for security."),
]


def _detect_language(code: str, language: Optional[str]) -> str:
    if language:
        return language.lower()
    if "def " in code or "import " in code or "class " in code and ":" in code:
        return "python"
    if "public class" in code or "void " in code or "System.out" in code:
        return "java"
    if "function " in code or "const " in code or "=>" in code:
        return "javascript"
    return "generic"


def _count_complexity(code: str) -> dict:
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    branch_keywords = re.findall(r"\b(if|elif|else|for|while|try|except|catch|switch|case)\b", code)
    return {
        "total_lines": len(lines),
        "code_lines": len(non_empty),
        "branches": len(branch_keywords),
        "complexity_note": (
            "High cyclomatic complexity — consider breaking into smaller functions."
            if len(branch_keywords) > 10
            else "Complexity looks manageable."
        ),
    }


def review_code(
    code: str,
    language: Optional[str] = None,
    context: Optional[str] = None,
) -> dict:
    """
    Review a code snippet and return structured feedback: detected issues,
    improvement suggestions, and a complexity assessment.

    Args:
        code: The source code to review (any language).
        language: Programming language hint — 'python', 'java', 'javascript', etc.
                  Auto-detected if not provided.
        context: Optional context about what the code does or what to focus on.

    Returns:
        Structured review with issues, suggestions, and complexity metrics.
    """
    if not code.strip():
        return {"error": "No code provided."}

    detected_lang = _detect_language(code, language)

    # Select patterns
    if detected_lang == "python":
        patterns = PYTHON_PATTERNS + GENERIC_PATTERNS
    elif detected_lang == "java":
        patterns = JAVA_PATTERNS + GENERIC_PATTERNS
    else:
        patterns = GENERIC_PATTERNS

    # Scan for issues
    issues = []
    lines = code.splitlines()
    for i, line in enumerate(lines, start=1):
        for pattern, message in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "line": i,
                    "code": line.strip()[:100],
                    "issue": message,
                    "severity": (
                        "high" if any(k in message.lower() for k in ["security", "credential", "secret", "risk"])
                        else "medium" if any(k in message.lower() for k in ["bare except", "generic exception", "global"])
                        else "low"
                    ),
                })

    # Deduplicate by issue message
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue["issue"], issue["line"])
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    unique_issues.sort(key=lambda x: severity_order.get(x["severity"], 3))

    # General suggestions
    suggestions = []
    if detected_lang == "python":
        if "def " in code and '"""' not in code and "'''" not in code:
            suggestions.append("Functions are missing docstrings — add them for maintainability.")
        if "type hint" not in code.lower() and "->" not in code and ": " not in code:
            suggestions.append("Consider adding type hints for better IDE support and readability.")
        if len(lines) > 50:
            suggestions.append("File is long — consider splitting into smaller modules.")
    elif detected_lang == "java":
        if "@Override" not in code and "extends" in code:
            suggestions.append("Missing @Override annotations on overriding methods.")
        if "final " not in code:
            suggestions.append("Consider marking immutable fields and parameters as final.")

    complexity = _count_complexity(code)

    return {
        "language_detected": detected_lang,
        "context": context or "No context provided.",
        "complexity": complexity,
        "issues_found": len(unique_issues),
        "issues": unique_issues,
        "suggestions": suggestions,
        "summary": (
            f"Found {len(unique_issues)} issue(s) in {complexity['code_lines']} lines of {detected_lang} code. "
            + (f"High severity: {sum(1 for i in unique_issues if i['severity'] == 'high')}. " if unique_issues else "")
            + complexity["complexity_note"]
        ),
    }

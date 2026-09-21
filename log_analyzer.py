"""
Log Analyzer Tool
Parses raw log text, extracts errors/warnings, and returns a structured summary.
"""

import re
from collections import Counter
from typing import Optional


def analyze_logs(
    log_text: str,
    max_errors: Optional[int] = 20,
) -> dict:
    """
    Analyze raw log output and return a structured summary of errors,
    warnings, and patterns to help diagnose issues quickly.

    Args:
        log_text: Raw log content (paste directly from terminal or log file).
        max_errors: Maximum number of distinct errors to return (default 20).

    Returns:
        A structured summary with error counts, top errors, warnings,
        stack traces, and a plain-English diagnosis.
    """
    lines = log_text.strip().splitlines()
    total_lines = len(lines)

    # Patterns
    error_pattern = re.compile(r"(error|exception|critical|fatal|traceback)", re.IGNORECASE)
    warning_pattern = re.compile(r"(warning|warn)", re.IGNORECASE)
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
    stack_trace_pattern = re.compile(r"(Traceback \(most recent call last\)|at \w+\.\w+\()", re.IGNORECASE)

    errors = []
    warnings = []
    stack_traces = []
    in_traceback = False
    current_trace = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_traceback and current_trace:
                stack_traces.append("\n".join(current_trace))
                current_trace = []
                in_traceback = False
            continue

        if stack_trace_pattern.search(stripped):
            in_traceback = True

        if in_traceback:
            current_trace.append(stripped)
            # End of traceback — usually a line like "SomeError: message"
            if re.match(r"^\w+Error|^\w+Exception", stripped) and len(current_trace) > 1:
                stack_traces.append("\n".join(current_trace))
                current_trace = []
                in_traceback = False
        elif error_pattern.search(stripped):
            errors.append(stripped)
        elif warning_pattern.search(stripped):
            warnings.append(stripped)

    if current_trace:
        stack_traces.append("\n".join(current_trace))

    # Deduplicate and count
    error_counts = Counter(errors)
    top_errors = [
        {"message": msg, "occurrences": count}
        for msg, count in error_counts.most_common(max_errors)
    ]

    warning_counts = Counter(warnings)
    top_warnings = [
        {"message": msg, "occurrences": count}
        for msg, count in warning_counts.most_common(10)
    ]

    # Time range
    timestamps = [
        timestamp_pattern.search(line).group()
        for line in lines
        if timestamp_pattern.search(line)
    ]
    time_range = {
        "start": timestamps[0] if timestamps else None,
        "end": timestamps[-1] if timestamps else None,
    }

    # Simple diagnosis
    diagnosis_parts = []
    if not errors and not stack_traces:
        diagnosis_parts.append("No errors or exceptions detected.")
    else:
        if stack_traces:
            diagnosis_parts.append(
                f"Found {len(stack_traces)} stack trace(s). "
                "Review the traces below for root cause."
            )
        if top_errors:
            most_common = top_errors[0]
            diagnosis_parts.append(
                f"Most frequent error ({most_common['occurrences']}x): "
                f"{most_common['message'][:120]}"
            )
    if warnings:
        diagnosis_parts.append(f"{len(warnings)} warning(s) found — may indicate upstream issues.")

    return {
        "summary": {
            "total_lines": total_lines,
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "stack_traces_found": len(stack_traces),
            "time_range": time_range,
        },
        "top_errors": top_errors,
        "top_warnings": top_warnings[:5],
        "stack_traces": stack_traces[:5],
        "diagnosis": " ".join(diagnosis_parts) or "Log parsed successfully.",
    }

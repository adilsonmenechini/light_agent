"""Observation categorization system for tool insights."""

from enum import Enum
from typing import Optional
import re


class ObservationCategory(str, Enum):
    """Categories for tool observations."""

    BUG = "bug"
    CONFIG = "config"
    DOCS = "docs"
    CODE = "code"
    DATABASE = "database"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    TEST = "test"
    PERFORMANCE = "performance"
    DEPENDENCY = "dependency"
    ERROR = "error"
    INFO = "info"
    UNKNOWN = "unknown"


# Keywords for each category
_CATEGORY_KEYWORDS = {
    ObservationCategory.BUG: [
        r"bug",
        r"fix",
        r"error",
        r"exception",
        r"fail",
        r"crash",
        r"broken",
        r"issue",
        r"defect",
        r"fault",
        r"malfunction",
    ],
    ObservationCategory.CONFIG: [
        r"config",
        r"settings?",
        r"yaml",
        r"json",
        r"toml",
        r"ini",
        r"env",
        r"environment",
        r"property",
        r"option",
        r"parameter",
        r"timeout",
        r"retry",
        r"limit",
        r"threshold",
    ],
    ObservationCategory.DOCS: [
        r"readme",
        r"documentation",
        r"docstring",
        r"comment",
        r"guide",
        r"tutorial",
        r"example",
        r"reference",
        r"manual",
    ],
    ObservationCategory.CODE: [
        r"import",
        r"class",
        r"function",
        r"method",
        r"variable",
        r"type",
        r"interface",
        r"enum",
        r"struct",
        r"def\s+\w+",
    ],
    ObservationCategory.DATABASE: [
        r"database",
        r"db",
        r"sql",
        r"query",
        r"table",
        r"column",
        r"schema",
        r"migration",
        r"postgres",
        r"mysql",
        r"sqlite",
        r"mongodb",
        r"redis",
        r"select",
        r"insert",
        r"update",
    ],
    ObservationCategory.SECURITY: [
        r"security",
        r"auth",
        r"token",
        r"password",
        r"secret",
        r"encryption",
        r"certificate",
        r"ssl",
        r"https",
        r"oauth",
        r"jwt",
        r"permission",
        r"access",
        r"vulnerability",
    ],
    ObservationCategory.DEPLOYMENT: [
        r"docker",
        r"kubernetes",
        r"k8s",
        r"deploy",
        r"pod",
        r"container",
        r"image",
        r"registry",
        r"helm",
        r"terraform",
    ],
    ObservationCategory.TEST: [
        r"test",
        r"pytest",
        r"unittest",
        r"coverage",
        r"assert",
        r"mock",
        r"fixture",
        r"spec",
        r"scenario",
        r"verify",
    ],
    ObservationCategory.PERFORMANCE: [
        r"performance",
        r"latency",
        r"throughput",
        r"memory",
        r"cpu",
        r"optimize",
        r"cache",
        r"benchmark",
        r"profiler",
        r"speed",
    ],
    ObservationCategory.DEPENDENCY: [
        r"dependency",
        r"package",
        r"import",
        r"require",
        r"install",
        r"npm",
        r"pip",
        r"uv",
        r"cargo",
        r"go.mod",
        r"poetry",
    ],
    ObservationCategory.ERROR: [
        r"error",
        r"failed",
        r"exception",
        r"traceback",
        r"raised",
        r"abort",
        r"panic",
        r"critical",
        r"fatal",
    ],
    ObservationCategory.INFO: [r"info", r"log", r"message", r"output", r"result", r"response"],
}

# Tool-to-category mapping
_TOOL_CATEGORY_MAP = {
    "read_file": ObservationCategory.CODE,
    "write_file": ObservationCategory.CODE,
    "edit": ObservationCategory.CODE,
    "exec": ObservationCategory.INFO,
    "grep": ObservationCategory.CODE,
    "glob": ObservationCategory.CODE,
    "list_dir": ObservationCategory.INFO,
    "web_search": ObservationCategory.DOCS,
    "web_fetch": ObservationCategory.DOCS,
    "github_check": ObservationCategory.CODE,
    "github_public": ObservationCategory.INFO,
    "gh_api_tool": ObservationCategory.INFO,
    "github_workflow_tool": ObservationCategory.DEPLOYMENT,
    "git_tool": ObservationCategory.CODE,
}


def _match_keywords(text: str, category: ObservationCategory) -> int:
    """Count keyword matches for a category in text."""
    if category not in _CATEGORY_KEYWORDS:
        return 0

    text_lower = text.lower()
    matches = 0
    for pattern in _CATEGORY_KEYWORDS[category]:
        if re.search(pattern, text_lower):
            matches += 1
    return matches


def categorize_tool_result(
    tool_name: str, tool_args: dict, tool_result: str
) -> ObservationCategory:
    """Categorize a tool result based on tool name, args, and result.

    Args:
        tool_name: Name of the tool that was executed.
        tool_args: Arguments passed to the tool.
        tool_result: Result returned by the tool.

    Returns:
        The most appropriate category for this observation.
    """
    # Combine tool args and result for analysis
    combined_text = f"{tool_args} {tool_result}"

    # First, check for strong keyword matches that override tool defaults
    # These are high-signal indicators
    priority_keywords = {
        "bug",
        "fix",
        "error",
        "failed",
        "exception",
        "crash",
        "database",
        "sql",
        "query",
        "postgres",
        "mysql",
        "mongodb",
        "docker",
        "kubernetes",
        "deploy",
        "container",
        "pod",
        "security",
        "auth",
        "token",
        "password",
        "secret",
        "jwt",
        "config",
        "yaml",
        "json",
        "env",
        "settings",
    }

    # Check if result starts with error indicators
    result_stripped = tool_result.strip().lower()
    error_indicators = ("error:", "failed", "exception", "traceback")

    # ERROR category takes precedence for error results
    if result_stripped.startswith(error_indicators):
        return ObservationCategory.ERROR

    # Count keyword matches for each category
    best_category = ObservationCategory.UNKNOWN
    best_score = 0
    category_scores: dict[ObservationCategory, int] = {}

    for category in ObservationCategory:
        if category == ObservationCategory.UNKNOWN:
            continue
        score = _match_keywords(combined_text, category)
        category_scores[category] = score
        if score > best_score:
            best_score = score
            best_category = category

    # If no keywords matched, use tool default
    if best_score == 0:
        if tool_name in _TOOL_CATEGORY_MAP:
            return _TOOL_CATEGORY_MAP[tool_name]
        return ObservationCategory.INFO

    # For tools with defaults, check if keyword score significantly exceeds default
    if tool_name in _TOOL_CATEGORY_MAP:
        default_category = _TOOL_CATEGORY_MAP[tool_name]
        default_score = category_scores.get(default_category, 0)
        # If another category has significantly more keywords, use it
        if best_score > default_score + 1:
            return best_category

    return best_category


def categorize_observation(insight: str, tool_name: str, tool_result: str) -> ObservationCategory:
    """Categorize an observation based on insight content and tool info.

    Args:
        insight: The extracted insight text.
        tool_name: Name of the tool that was executed.
        tool_result: Result returned by the tool.

    Returns:
        The most appropriate category for this observation.
    """
    # Combine insight with tool info for richer categorization
    combined_text = f"{insight} {tool_result}"

    # Use the same categorization logic
    return categorize_tool_result(tool_name, {}, combined_text)


def get_category_description(category: ObservationCategory) -> str:
    """Get a human-readable description for a category.

    Args:
        category: The category to describe.

    Returns:
        A brief description of what the category represents.
    """
    descriptions = {
        ObservationCategory.BUG: "Bug reports and fixes",
        ObservationCategory.CONFIG: "Configuration settings and properties",
        ObservationCategory.DOCS: "Documentation and reference materials",
        ObservationCategory.CODE: "Code and programming-related findings",
        ObservationCategory.DATABASE: "Database queries and schema changes",
        ObservationCategory.SECURITY: "Security and authentication details",
        ObservationCategory.DEPLOYMENT: "Deployment and infrastructure",
        ObservationCategory.TEST: "Test cases and coverage",
        ObservationCategory.PERFORMANCE: "Performance and optimization",
        ObservationCategory.DEPENDENCY: "Package dependencies",
        ObservationCategory.ERROR: "Errors and exceptions",
        ObservationCategory.INFO: "General information and logs",
        ObservationCategory.UNKNOWN: "Uncategorized",
    }
    return descriptions.get(category, "Uncategorized")


def get_all_categories() -> list[ObservationCategory]:
    """Get all available observation categories.

    Returns:
        A list of all category values.
    """
    return list(ObservationCategory)

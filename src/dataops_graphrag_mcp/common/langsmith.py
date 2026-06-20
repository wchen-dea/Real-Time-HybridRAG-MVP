import os
from dataops_graphrag_mcp.common.logging import get_logger
from dataops_graphrag_mcp.common.settings import settings

_logger = get_logger(__name__)


def is_langsmith_enabled() -> bool:
    return bool(settings.langsmith_tracing and settings.langsmith_api_key)


def configure_langsmith() -> bool:
    if not settings.langsmith_tracing:
        return False
    if not settings.langsmith_api_key:
        _logger.warning(
            "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing; tracing disabled."
        )
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True


def langsmith_tags(environment: str | None = None) -> list[str]:
    tags = [tag.strip() for tag in settings.langsmith_tags.split(",") if tag.strip()]
    if settings.app_env:
        tags.append(f"app_env:{settings.app_env}")
    if environment:
        tags.append(f"request_env:{environment}")
    return sorted(set(tags))

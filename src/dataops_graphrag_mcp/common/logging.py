import logging
from dataops_graphrag_mcp.common.settings import settings


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=settings.log_level)
    return logging.getLogger(name)

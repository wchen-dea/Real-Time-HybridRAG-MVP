from dataops_graphrag_mcp.common.settings import settings


def get_chat_model():
    if settings.llm_provider.lower() == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.anthropic_temperature,
            max_tokens=settings.anthropic_max_tokens,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

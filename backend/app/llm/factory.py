from app.core.config import settings
from app.core.exceptions import ChatBotException
from app.llm.base import LLMProvider
from app.llm.providers.mock import MockProvider
from app.llm.providers.openai_provider import OpenAIProvider

# provider 单例缓存（Provider 无状态，进程内复用安全）
_instances: dict[str, LLMProvider] = {}

# Provider 展示信息（T08 /providers 端点使用）
_PROVIDER_META: dict[str, dict] = {
    "mock": {"display_name": "Mock（测试）", "models": ["mock-chat"]},
    "xingchen": {"display_name": "星辰大模型", "models": ["xingchen-pro"]},
    "openai": {"display_name": "OpenAI", "models": ["gpt-4o-mini"]},
}

# 各 Provider 所需的配置键：配置为空视为不可用
_PROVIDER_REQUIRED: dict[str, list[str]] = {
    "mock": [],
    "xingchen": ["xingchen_api_key", "xingchen_base_url"],
    "openai": ["openai_api_key"],
}


def get_provider(name: str) -> LLMProvider:
    """按名称获取 Provider 单例；未知名称抛 400"""
    if name in _instances:
        return _instances[name]

    if name == "mock":
        provider: LLMProvider = MockProvider()
    elif name == "xingchen":
        # 星辰大模型走 OpenAI 兼容协议，仅 base_url / api_key / 默认模型不同
        provider = OpenAIProvider(
            api_key=settings.xingchen_api_key,
            base_url=settings.xingchen_base_url,
            name="xingchen",
        )
    elif name == "openai":
        provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            name="openai",
        )
    else:
        raise ChatBotException("PROVIDER_NOT_FOUND", f"未知的 LLM Provider: {name}", 400)

    _instances[name] = provider
    return provider


def get_available_providers() -> list[dict]:
    """返回当前配置下可用的 Provider 列表（供前端模型选择器）"""
    available = []
    for name, meta in _PROVIDER_META.items():
        missing = [
            key
            for key in _PROVIDER_REQUIRED.get(name, [])
            if not getattr(settings, key, "")
        ]
        if missing:
            continue
        available.append({"name": name, **meta})
    return available

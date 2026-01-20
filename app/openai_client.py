
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import requests

from .config import OpenAISettings
from .utils import setup_logging

logger = setup_logging()

# Cache for Azure AD token
_token_cache: Dict[str, Any] = {}


def _get_azure_ad_token() -> str:
    """Get Azure AD token for Azure OpenAI using DefaultAzureCredential."""
    import time as _time
    
    # Check cache
    if _token_cache.get("token") and _token_cache.get("expires_at", 0) > _time.time() + 60:
        return _token_cache["token"]
    
    try:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        _token_cache["token"] = token.token
        _token_cache["expires_at"] = token.expires_on
        logger.info("Obtained Azure AD token for OpenAI")
        return token.token
    except Exception as e:
        logger.error(f"Failed to get Azure AD token: {e}")
        raise OpenAIClientError(f"Failed to get Azure AD token: {e}")


class OpenAIClientError(Exception):
    pass


def chat_completion(
    settings: OpenAISettings,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1200,
    max_retries: int = 3,
    retry_backoff: float = 1.5,
    deployment_override: str | None = None,
    model_override: str | None = None,
    api_version_override: str | None = None,
) -> Dict[str, Any]:
    """Call Azure OpenAI / Foundry chat completions with retry logic.

    Uses the v1-style chat completions endpoint:
        POST {endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=...
    
    Args:
        settings: OpenAI configuration settings
        messages: List of chat messages
        temperature: Sampling temperature (0.0 = deterministic)
        max_tokens: Maximum tokens in response
        max_retries: Number of retry attempts
        retry_backoff: Exponential backoff multiplier
        deployment_override: Optional deployment name to use instead of settings.deployment_name
        model_override: Optional model name to use instead of settings.model_name
        api_version_override: Optional API version to use instead of settings.api_version
    """
    # Validate settings - api_key is optional when using Azure AD
    if not settings.endpoint or not settings.deployment_name:
        raise OpenAIClientError(
            "Azure OpenAI settings are incomplete. "
            "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT_NAME."
        )
    
    if not settings.use_azure_ad and not settings.api_key:
        raise OpenAIClientError(
            "Azure OpenAI authentication not configured. "
            "Either set AZURE_OPENAI_API_KEY or enable Azure AD auth with AZURE_OPENAI_USE_AZURE_AD=true."
        )

    deployment = deployment_override or settings.deployment_name
    model = model_override or settings.model_name
    api_version = api_version_override or settings.api_version

    url = f"{settings.endpoint}/openai/deployments/{deployment}/chat/completions"
    params = {"api-version": api_version}
    
    # Build headers based on auth method
    headers = {"Content-Type": "application/json"}
    if settings.use_azure_ad:
        token = _get_azure_ad_token()
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["api-key"] = settings.api_key

    body = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "model": model,
    }

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, params=params, json=body, timeout=60)
            if resp.status_code >= 400:
                raise OpenAIClientError(
                    f"OpenAI API error {resp.status_code}: {resp.text}"
                )

            data = resp.json()
            try:
                choice = data["choices"][0]
                content = choice["message"]["content"]
            except Exception as exc:
                raise OpenAIClientError(
                    f"Unexpected OpenAI response: {json.dumps(data)}"
                ) from exc

            usage = data.get("usage", {})
            return {"content": content, "usage": usage}

        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.warning(
                "OpenAI chat_completion attempt %s failed: %s", attempt, str(exc)
            )
            if attempt < max_retries:
                time.sleep(retry_backoff**attempt)

    raise OpenAIClientError(f"OpenAI chat_completion failed after {max_retries} attempts: {last_err}")

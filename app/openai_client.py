
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


def _call_openai_endpoint(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, str],
    body: Dict[str, Any],
    endpoint_name: str = "primary",
) -> Dict[str, Any]:
    """Make a single call to an OpenAI endpoint."""
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
    logger.debug("Successfully called %s endpoint", endpoint_name)
    return {"content": content, "usage": usage}


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
    """Call Azure OpenAI / Foundry chat completions with retry logic and fallback.

    Uses the v1-style chat completions endpoint:
        POST {endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=...
    
    If a fallback endpoint is configured and the primary returns 429 (rate limit),
    the request will automatically be retried on the fallback endpoint.
    
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

    # Primary endpoint configuration
    primary_url = f"{settings.endpoint}/openai/deployments/{deployment}/chat/completions"
    primary_params = {"api-version": api_version}
    primary_headers = {"Content-Type": "application/json"}
    if settings.use_azure_ad:
        token = _get_azure_ad_token()
        primary_headers["Authorization"] = f"Bearer {token}"
    else:
        primary_headers["api-key"] = settings.api_key

    # Check if fallback is configured
    has_fallback = bool(settings.fallback_endpoint and (settings.fallback_api_key or settings.fallback_use_azure_ad))
    fallback_url = None
    fallback_headers = None
    fallback_params = None
    
    if has_fallback:
        fallback_deployment = settings.fallback_deployment_name or deployment
        fallback_api_version = settings.fallback_api_version or api_version
        fallback_url = f"{settings.fallback_endpoint}/openai/deployments/{fallback_deployment}/chat/completions"
        fallback_params = {"api-version": fallback_api_version}
        fallback_headers = {"Content-Type": "application/json"}
        if settings.fallback_use_azure_ad:
            # Use same Azure AD token for fallback (same tenant)
            token = _get_azure_ad_token()
            fallback_headers["Authorization"] = f"Bearer {token}"
        else:
            fallback_headers["api-key"] = settings.fallback_api_key

    body = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "model": model,
    }

    last_err: Exception | None = None
    used_fallback = False
    used_mini = False
    actual_attempts = 0  # Track actual attempts (not endpoint switches)
    max_actual_retries = 5  # More retries with proper waits
    
    # Check if we have a mini model configured for tertiary fallback
    has_mini = bool(settings.chat_deployment_name)
    mini_url = None
    mini_headers = None
    mini_params = None
    mini_body = None
    
    if has_mini:
        mini_deployment = settings.chat_deployment_name
        mini_api_version = settings.chat_api_version or api_version
        mini_model = settings.chat_model_name or "gpt-4.1-mini"
        mini_url = f"{settings.endpoint}/openai/deployments/{mini_deployment}/chat/completions"
        mini_params = {"api-version": mini_api_version}
        mini_headers = {"Content-Type": "application/json"}
        if settings.use_azure_ad:
            token = _get_azure_ad_token()
            mini_headers["Authorization"] = f"Bearer {token}"
        else:
            mini_headers["api-key"] = settings.api_key
        mini_body = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": mini_model,
        }
    
    while actual_attempts < max_actual_retries:
        try:
            # Try mini model if both primary and fallback are rate limited
            if used_mini:
                return _call_openai_endpoint(mini_url, mini_headers, mini_params, mini_body, "mini")
            # Try primary endpoint first
            elif not used_fallback:
                return _call_openai_endpoint(primary_url, primary_headers, primary_params, body, "primary")
            else:
                # Already switched to fallback
                return _call_openai_endpoint(fallback_url, fallback_headers, fallback_params, body, "fallback")

        except Exception as exc:  # noqa: BLE001
            last_err = exc
            is_rate_limited = "429" in str(exc) or "RateLimitReached" in str(exc)
            
            logger.warning(
                "OpenAI chat_completion attempt failed: %s", str(exc)
            )
            
            # If rate limited and we have a fallback, switch to it (don't count as attempt)
            if is_rate_limited and has_fallback and not used_fallback and not used_mini:
                logger.info("Rate limited on primary endpoint - switching to fallback endpoint")
                used_fallback = True
                continue  # Don't increment attempt counter
            
            # If rate limited on fallback too, try mini model (don't count as attempt)
            if is_rate_limited and used_fallback and has_mini and not used_mini:
                logger.info("Rate limited on fallback endpoint - switching to gpt-4.1-mini")
                used_mini = True
                continue  # Don't increment attempt counter
            
            # Now count this as an actual attempt
            actual_attempts += 1
            
            if actual_attempts < max_actual_retries:
                if is_rate_limited:
                    # Azure OpenAI says wait 60 seconds - actually wait
                    wait_time = 62  # 60 + 2 buffer
                    logger.info("Rate limited (429) - waiting %s seconds before retry (attempt %d/%d)", 
                               wait_time, actual_attempts, max_actual_retries)
                else:
                    wait_time = retry_backoff ** actual_attempts
                time.sleep(wait_time)

    raise OpenAIClientError(f"OpenAI chat_completion failed after {actual_attempts} attempts: {last_err}")

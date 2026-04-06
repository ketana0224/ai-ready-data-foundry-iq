"""Create Foundry IQ knowledge source and knowledge base from spec.

This script uses Entra ID authentication (DefaultAzureCredential) and Azure AI Search
preview APIs for knowledgesources/knowledgebases.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import requests
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

DEFAULT_API_VERSION = "2025-11-01-preview"
SEARCH_SCOPE = "https://search.azure.com/.default"


def _get_env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(f"Environment variable '{name}' is required.")
    return value or ""


def _parse_csv_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_api_version(api_version: str) -> None:
    # knowledge source / knowledge base APIs are currently preview-only.
    if "preview" not in api_version:
        raise ValueError(
            "AI_SEARCH_API_VERSION must be a preview version for Foundry IQ APIs "
            f"(for example: {DEFAULT_API_VERSION}). Current value: {api_version}"
        )


def _auth_headers(credential: DefaultAzureCredential) -> Dict[str, str]:
    token = credential.get_token(SEARCH_SCOPE).token
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;odata.metadata=minimal",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _put_json(
    endpoint: str,
    path: str,
    api_version: str,
    payload: Dict[str, Any],
    credential: DefaultAzureCredential,
) -> Dict[str, Any]:
    url = f"{endpoint.rstrip('/')}{path}"
    response = requests.put(
        url,
        params={"api-version": api_version},
        headers=_auth_headers(credential),
        json=payload,
        timeout=60,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Request failed: {response.status_code} {response.reason}\n"
            f"URL: {response.url}\n"
            f"Response: {response.text}"
        )

    try:
        return response.json()
    except requests.JSONDecodeError:
        return {"raw": response.text}


def _post_json(
    endpoint: str,
    path: str,
    api_version: str,
    payload: Dict[str, Any],
    credential: DefaultAzureCredential,
) -> Dict[str, Any]:
    url = f"{endpoint.rstrip('/')}{path}"
    response = requests.post(
        url,
        params={"api-version": api_version},
        headers=_auth_headers(credential),
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Request failed: {response.status_code} {response.reason}\n"
            f"URL: {response.url}\n"
            f"Response: {response.text}"
        )

    try:
        return response.json()
    except requests.JSONDecodeError:
        return {"raw": response.text}


def main() -> int:
    load_dotenv()

    search_endpoint = _get_env("AI_SEARCH_ENDPOINT")
    index_name = _get_env("AI_SEARCH_INDEX_NAME")
    semantic_config = _get_env("AI_SEARCH_SEMANTIC")
    api_version = _get_env("AI_SEARCH_API_VERSION", required=False, default=DEFAULT_API_VERSION)

    knowledge_source_name = _get_env("KNOWLEDGE_SOURCE_NAME")
    knowledge_base_name = _get_env("KNOWLEDGE_BASE_NAME")
    knowledge_source_description = _get_env("KNOWLEDGE_SOURCE_DESCRIPTION", required=False, default="")
    knowledge_base_description = _get_env("KNOWLEDGE_BASE_DESCRIPTION", required=False, default="")
    search_fields_csv = _get_env(
        "AI_SEARCH_FIELDS",
        required=False,
        default="contentVector,keywords,summary",
    )

    aoai_endpoint = _get_env("AZURE_OPENAI_API_ENDPOINT")
    aoai_model = _get_env("AZURE_OPENAI_MODEL")
    aoai_deployment = _get_env("AZURE_OPENAI_DEPLOYMENT_ID", required=False, default=aoai_model)
    run_retrieve_test = _to_bool(_get_env("RUN_RETRIEVE_TEST", required=False, default="false"))
    retrieve_test_query = _get_env(
        "RETRIEVE_TEST_QUERY",
        required=False,
        default="このナレッジベースの対象領域を要約して",
    )

    _validate_api_version(api_version)
    search_fields = _parse_csv_list(search_fields_csv)
    if not search_fields:
        raise ValueError("AI_SEARCH_FIELDS must contain at least one field name.")

    credential = DefaultAzureCredential()

    knowledge_source_payload: Dict[str, Any] = {
        "name": knowledge_source_name,
        "kind": "searchIndex",
        "description": knowledge_source_description,
        "searchIndexParameters": {
            "searchIndexName": index_name,
            "semanticConfigurationName": semantic_config,
            "sourceDataFields": [{"name": "content"}],
            "searchFields": [{"name": field_name} for field_name in search_fields],
        },
    }

    knowledge_base_payload: Dict[str, Any] = {
        "name": knowledge_base_name,
        "description": knowledge_base_description,
        "knowledgeSources": [{"name": knowledge_source_name}],
        "retrievalReasoningEffort": {"kind": "medium"},
        "outputMode": "answerSynthesis",
        "retrievalInstructions": "Always use the configured knowledge source unless query scope is clearly out-of-domain.",
        "answerInstructions": "Synthesize a concise answer grounded in citations from retrieved content.",
        "models": [
            {
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": aoai_endpoint,
                    "deploymentId": aoai_deployment,
                    "modelName": aoai_model,
                },
            }
        ],
    }

    source_result = _put_json(
        endpoint=search_endpoint,
        path=f"/knowledgesources('{knowledge_source_name}')",
        api_version=api_version,
        payload=knowledge_source_payload,
        credential=credential,
    )
    print("[OK] knowledge source created/updated")
    print(json.dumps(source_result, ensure_ascii=False, indent=2))

    base_result = _put_json(
        endpoint=search_endpoint,
        path=f"/knowledgebases('{knowledge_base_name}')",
        api_version=api_version,
        payload=knowledge_base_payload,
        credential=credential,
    )
    print("[OK] knowledge base created/updated")
    print(json.dumps(base_result, ensure_ascii=False, indent=2))

    if run_retrieve_test:
        retrieve_payload: Dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": retrieve_test_query}],
                }
            ],
            "outputMode": "answerSynthesis",
            "includeActivity": True,
            "retrievalReasoningEffort": {"kind": "medium"},
        }
        retrieve_result = _post_json(
            endpoint=search_endpoint,
            path=f"/knowledgebases('{knowledge_base_name}')/retrieve",
            api_version=api_version,
            payload=retrieve_payload,
            credential=credential,
        )
        print("[OK] retrieve test succeeded")
        print(json.dumps(retrieve_result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise

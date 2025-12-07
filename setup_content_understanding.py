#!/usr/bin/env python3
"""
One-time setup script for Azure Content Understanding.
Configures default model deployments required by prebuilt analyzers.
"""

import os
import sys
from pathlib import Path
import json

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def configure_defaults():
    """Configure default model deployments for Content Understanding."""
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    use_azure_ad = os.getenv("AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD", "true").lower() == "true"
    
    if not endpoint:
        print("❌ AZURE_CONTENT_UNDERSTANDING_ENDPOINT not set")
        return False
    
    # Get authentication
    headers = {}
    if use_azure_ad:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
            print("✅ Using Azure AD authentication")
        except ImportError:
            print("❌ azure-identity not installed. Run: uv add azure-identity")
            return False
        except Exception as e:
            print(f"❌ Failed to get Azure AD token: {e}")
            print("   Run: az login")
            return False
    elif api_key:
        headers["Ocp-Apim-Subscription-Key"] = api_key
        print("✅ Using API key authentication")
    else:
        print("❌ No authentication method configured")
        return False
    
    headers["Content-Type"] = "application/merge-patch+json"
    headers["x-ms-useragent"] = "underwriting-assistant-setup"
    
    # Prompt for model deployment names
    print("\n" + "="*60)
    print("Azure Content Understanding - Model Deployment Setup")
    print("="*60)
    print("\nPrebuilt analyzers require specific model deployments.")
    print("You need to deploy these models in Azure AI Foundry first:")
    print("  • GPT-4.1 (for general analyzers)")
    print("  • GPT-4.1-mini (for RAG analyzers like documentSearch)")
    print("  • text-embedding-3-large (for embeddings)")
    print("\n" + "="*60 + "\n")
    
    print("Enter your model deployment names:")
    gpt_41_deployment = input("GPT-4.1 deployment name (default: gpt-4.1): ").strip() or "gpt-4.1"
    gpt_41_mini_deployment = input("GPT-4.1-mini deployment name (default: gpt-4.1-mini): ").strip() or "gpt-4.1-mini"
    text_embedding_deployment = input("text-embedding-3-large deployment name (default: text-embedding-3-large): ").strip() or "text-embedding-3-large"
    
    print(f"\n📋 Configuring defaults:")
    print(f"   Endpoint: {endpoint}")
    print(f"   gpt-4.1 → {gpt_41_deployment}")
    print(f"   gpt-4.1-mini → {gpt_41_mini_deployment}")
    print(f"   text-embedding-3-large → {text_embedding_deployment}")
    
    # Prepare request
    url = f"{endpoint}/contentunderstanding/defaults?api-version={api_version}"
    body = {
        "modelDeployments": {
            "gpt-4.1": gpt_41_deployment,
            "gpt-4.1-mini": gpt_41_mini_deployment,
            "text-embedding-3-large": text_embedding_deployment,
        }
    }
    
    # Send request
    try:
        print("\n⏳ Sending configuration request...")
        print(f"   URL: {url}")
        print(f"   Body: {json.dumps(body, indent=2)}")
        
        
        response = requests.patch(url, headers=headers, json=body, timeout=30)
        
        if response.ok:
            result = response.json()
            print("\n✅ Defaults configured successfully!")
            print("\nConfigured model mappings:")
            for model, deployment in result.get("modelDeployments", {}).items():
                print(f"  {model} → {deployment}")
            print("\n🎉 You can now use prebuilt analyzers!")
            return True
        else:
            print(f"\n❌ Configuration failed: {response.status_code} {response.reason}")
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_info = error_json["error"]
                    print(f"   Error Code: {error_info.get('code')}")
                    print(f"   Error Message: {error_info.get('message')}")
                else:
                    print(f"   Response: {error_json}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False


def verify_configuration():
    """Verify that defaults are configured."""
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    use_azure_ad = os.getenv("AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD", "true").lower() == "true"
    
    # Get authentication
    headers = {}
    if use_azure_ad:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
        except Exception:
            return False
    elif api_key:
        headers["Ocp-Apim-Subscription-Key"] = api_key
    else:
        return False
    
    headers["x-ms-useragent"] = "underwriting-assistant-setup"
    
    url = f"{endpoint}/contentunderstanding/defaults?api-version={api_version}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.ok:
            result = response.json()
            model_deployments = result.get("modelDeployments", {})
            if model_deployments:
                print("\n✅ Current defaults configuration:")
                for model, deployment in model_deployments.items():
                    print(f"  {model} → {deployment}")
                return True
        return False
    except:
        return False


if __name__ == "__main__":
    print("Azure Content Understanding - Setup Utility\n")
    
    # Check if defaults are already configured
    if verify_configuration():
        print("\n⚠️  Defaults are already configured.")
        response = input("Do you want to reconfigure? (y/N): ").strip().lower()
        if response != 'y':
            print("Exiting without changes.")
            sys.exit(0)
    
    # Configure defaults
    if configure_defaults():
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check your configuration and try again.")
        sys.exit(1)

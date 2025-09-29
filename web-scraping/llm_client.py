#!/usr/bin/env python3
"""
LLM Client - Unified interface for multiple LLM providers
Supports OpenAI, Anthropic, Azure OpenAI with environment-based configuration
"""
import os
import logging
from typing import Dict, List, Optional, Any, Generator, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: str
    max_tokens: int = 1000
    temperature: float = 0.7
    base_url: Optional[str] = None
    api_version: Optional[str] = None

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    finish_reason: str = "completed"
    sources: List[Dict] = None

class LLMClient:
    def __init__(self):
        self.providers = {}
        self.default_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
        self.fallback_model = os.getenv('FALLBACK_MODEL', 'gpt-3.5-turbo')
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers based on environment variables"""
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            self.providers[LLMProvider.OPENAI] = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
                temperature=float(os.getenv('TEMPERATURE', 0.7))
            )
            logger.info("Initialized OpenAI provider")
        
        # Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            self.providers[LLMProvider.ANTHROPIC] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model='claude-3-sonnet-20240229',
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
                temperature=float(os.getenv('TEMPERATURE', 0.7))
            )
            logger.info("Initialized Anthropic provider")
        
        # Azure OpenAI
        if os.getenv('AZURE_OPENAI_API_KEY'):
            self.providers[LLMProvider.AZURE_OPENAI] = LLMConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                base_url=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_OPENAI_VERSION'),
                max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
                temperature=float(os.getenv('TEMPERATURE', 0.7))
            )
            logger.info("Initialized Azure OpenAI provider")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [provider.value for provider in self.providers.keys()]
    
    def generate_completion(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Generate completion using specified provider"""
        
        # Determine provider
        if provider is None:
            provider = self.default_provider
        
        provider_enum = LLMProvider(provider)
        if provider_enum not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        config = self.providers[provider_enum]
        
        # Override config if specified
        if model:
            config.model = model
        if max_tokens:
            config.max_tokens = max_tokens
        if temperature is not None:
            config.temperature = temperature
        
        try:
            if provider_enum == LLMProvider.OPENAI:
                return self._openai_completion(config, prompt, system_prompt, context)
            elif provider_enum == LLMProvider.ANTHROPIC:
                return self._anthropic_completion(config, prompt, system_prompt, context)
            elif provider_enum == LLMProvider.AZURE_OPENAI:
                return self._azure_openai_completion(config, prompt, system_prompt, context)
            else:
                raise ValueError(f"Provider {provider} not implemented")
        
        except Exception as e:
            logger.error(f"Error with provider {provider}: {e}")
            # Try fallback if available
            if provider != self.default_provider and self.default_provider in [p.value for p in self.providers.keys()]:
                logger.info(f"Falling back to {self.default_provider}")
                return self.generate_completion(
                    prompt, self.default_provider, self.fallback_model, 
                    max_tokens, temperature, system_prompt, context
                )
            raise
    
    def _openai_completion(
        self, 
        config: LLMConfig, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Generate completion using OpenAI"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=config.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if context:
                # Add context as assistant messages or user context
                for ctx in context[:3]:  # Limit context
                    messages.append({"role": "user", "content": f"Context: {ctx.get('content', '')}"})
            
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=config.model,
                provider=config.provider.value,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason
            )
        
        except ImportError:
            raise ValueError("OpenAI package not installed. Run: uv add openai")
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _anthropic_completion(
        self, 
        config: LLMConfig, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Generate completion using Anthropic"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.api_key)
            
            # Build full prompt
            full_prompt = ""
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"
            
            if context:
                full_prompt += "Context:\n"
                for ctx in context[:3]:
                    full_prompt += f"- {ctx.get('content', '')}\n"
                full_prompt += "\n"
            
            full_prompt += f"Human: {prompt}\n\nAssistant:"
            
            response = client.completions.create(
                model=config.model,
                prompt=full_prompt,
                max_tokens_to_sample=config.max_tokens,
                temperature=config.temperature
            )
            
            return LLMResponse(
                content=response.completion,
                model=config.model,
                provider=config.provider.value,
                tokens_used=0,  # Anthropic doesn't provide token count in older API
                finish_reason="completed"
            )
        
        except ImportError:
            raise ValueError("Anthropic package not installed. Run: uv add anthropic")
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")
    
    def _azure_openai_completion(
        self, 
        config: LLMConfig, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Generate completion using Azure OpenAI"""
        try:
            import openai
            
            client = openai.AzureOpenAI(
                api_key=config.api_key,
                api_version=config.api_version,
                azure_endpoint=config.base_url
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if context:
                for ctx in context[:3]:
                    messages.append({"role": "user", "content": f"Context: {ctx.get('content', '')}"})
            
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=config.model,
                provider=config.provider.value,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason
            )
        
        except ImportError:
            raise ValueError("OpenAI package not installed. Run: uv add openai")
        except Exception as e:
            raise Exception(f"Azure OpenAI API error: {e}")
    
    def generate_rag_response(
        self,
        query: str,
        context_documents: List[Dict],
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None
    ) -> LLMResponse:
        """Generate RAG response with retrieved context"""
        
        # Default RAG system prompt
        if not system_prompt:
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
            Use the context information to provide accurate, relevant answers. 
            If you cannot answer based on the context, say so clearly.
            Always cite your sources when possible."""
        
        # Format context
        context_text = "\n\n".join([
            f"Source {i+1}: {doc.get('content', '')}"
            for i, doc in enumerate(context_documents[:5])
        ])
        
        # Create RAG prompt
        rag_prompt = f"""Context Information:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to answer the question, please indicate that clearly."""
        
        # Generate response
        response = self.generate_completion(
            prompt=rag_prompt,
            system_prompt=system_prompt,
            provider=provider,
            context=context_documents
        )
        
        # Add sources to response
        response.sources = [
            {
                "id": doc.get("id", ""),
                "content": doc.get("content", "")[:200] + "...",
                "metadata": doc.get("metadata", {})
            }
            for doc in context_documents[:int(os.getenv('RAG_MAX_SOURCES', 5))]
        ]
        
        return response

# Global LLM client instance
llm_client = LLMClient()

# Convenience functions
def generate_completion(prompt: str, **kwargs) -> LLMResponse:
    """Quick completion generation"""
    return llm_client.generate_completion(prompt, **kwargs)

def generate_rag_response(query: str, context_documents: List[Dict], **kwargs) -> LLMResponse:
    """Quick RAG response generation"""
    return llm_client.generate_rag_response(query, context_documents, **kwargs)

def get_available_providers() -> List[str]:
    """Get available LLM providers"""
    return llm_client.get_available_providers()

if __name__ == "__main__":
    # Test the LLM client
    print("Available providers:", get_available_providers())
    
    # Test completion
    try:
        response = generate_completion("What is the capital of France?")
        print(f"Response: {response.content}")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
    except Exception as e:
        print(f"Error: {e}")
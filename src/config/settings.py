"""Configuration settings for Intelligent Procurement Assistant."""
from typing import List, Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration loaded dynamically from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Provider Selection: 'gemini' | 'openai' | 'openrouter' | 'ollama'
    llm_provider: str = Field(default="gemini", description="Active LLM Provider")
    ai_model: str = Field(default="gemini-2.5-flash", description="Active AI Model identifier")

    # Dynamic Model Catalogs (configured via environment or .env)
    gemini_models: str = Field(
        default="gemini-2.5-flash,gemini-2.5-pro,gemini-1.5-pro,gemini-1.5-flash",
        description="Comma-separated Gemini model identifiers"
    )
    openai_models: str = Field(
        default="gpt-4o,gpt-4o-mini,o3-mini,gpt-4-turbo",
        description="Comma-separated OpenAI model identifiers"
    )
    openrouter_models: str = Field(
        default="anthropic/claude-3.5-sonnet,deepseek/deepseek-r1,meta-llama/llama-3.3-70b-instruct,google/gemini-2.5-flash,mistralai/mistral-large-2411",
        description="Comma-separated OpenRouter model identifiers"
    )
    ollama_models: str = Field(
        default="llama3.2,mistral,qwen2.5:7b,deepseek-r1:8b,phi4,llava",
        description="Comma-separated Ollama model identifiers"
    )

    # API Keys & Endpoints
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI Base URL")
    openrouter_api_key: str = Field(default="", description="OpenRouter API Key")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter Base URL")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", description="Ollama Local Base URL")

    # Application Defaults
    usd_inr_rate: float = Field(default=84.0, description="Standard USD to INR conversion rate")
    dataset_dir: str = Field(default="./vendor_dataset", description="Directory storing generated vendor bid files")
    app_title: str = Field(default="Autonomous RFx Normalization & Interrogation Engine", description="Application Title")
    debug: bool = Field(default=False, description="Enable debug logging")

    def get_models_for_provider(self, provider: str) -> List[str]:
        """Dynamically retrieve model list for a given provider based on configuration."""
        p = provider.lower().strip()
        raw_str = ""
        if p == "gemini":
            raw_str = self.gemini_models
        elif p == "openai":
            raw_str = self.openai_models
        elif p == "openrouter":
            raw_str = self.openrouter_models
        elif p == "ollama":
            raw_str = self.ollama_models

        models = [m.strip() for m in raw_str.split(",") if m.strip()]
        
        # Ensure configured ai_model is present in the list if provider matches
        if p == self.llm_provider.lower() and self.ai_model and self.ai_model not in models:
            models.insert(0, self.ai_model)
            
        return models if models else [self.ai_model]


def get_settings() -> AppSettings:
    """Retrieve an instance of application settings."""
    return AppSettings()

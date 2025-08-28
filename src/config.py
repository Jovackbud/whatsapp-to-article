import os
from dotenv import load_dotenv
from typing import List, Optional, FrozenSet

# Load environment variables
load_dotenv()

class Config:
    """
    Configuration settings for the WhatsApp to Article Converter application.
    Manages LLM parameters, file handling limits, export defaults, and Streamlit page settings.
    """
    # LLM Configuration (developer-configurable)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # File handling settings
    SUPPORTED_FILE_TYPES: FrozenSet[str] = frozenset({"txt", "docx", "pdf"})
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    MAX_TEXT_LENGTH: int = 50000  # characters
    
    # Export settings
    DEFAULT_TITLE: str = "Converted Chat Article"
    
    # Streamlit page config
    PAGE_TITLE: str = "WhatsApp to Article Converter"
    PAGE_ICON: str = "📝"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please ensure it's set in your .env file or environment.")
        return True
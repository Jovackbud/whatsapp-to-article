import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # LLM Configuration (developer-configurable)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # File handling settings
    SUPPORTED_FILE_TYPES = ["txt", "docx", "pdf"]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TEXT_LENGTH = 50000  # characters
    
    # Export settings
    DEFAULT_TITLE = "Converted Chat Article"
    
    # Streamlit page config
    PAGE_TITLE = "WhatsApp to Article Converter"
    PAGE_ICON = "📝"
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        return True
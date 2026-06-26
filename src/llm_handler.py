import os
import logging
from typing import Optional, Dict, Tuple, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from .config import Config

logger = logging.getLogger(__name__)


class GeminiHandler:
    """
    Handles interactions with the Google Gemini LLM using LangChain.
    Bypasses REST API restrictions in cloud environments using gRPC.
    """

    def __init__(self):
        """Initializes the Gemini handler by validating config and setting up the model."""
        try:
            Config.validate_config()
            self.model_name = Config.GEMINI_MODEL
            self.temperature = 0.7
            self.max_output_tokens = 8192
            self.model = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=Config.GOOGLE_API_KEY,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                verbose=False,
            )
            logger.info(f"Gemini client initialized for model '{self.model_name}'.")
        except ValueError as ve:
            logger.error(f"Configuration error: {ve}")
            raise
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini model: {e}")
            raise RuntimeError(
                f"Failed to initialize Gemini model. "
                f"Please check your API key and configuration. Error: {e}"
            )

    def _load_system_prompt(self) -> str:
        """Load the system prompt from file. Falls back to embedded default."""
        prompt_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "prompts", "conversion_prompt_system.txt"
        )
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                logger.info(f"Loaded system prompt from {prompt_file}")
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"System prompt not found at {prompt_file}. Using embedded fallback.")
            return (
                "You are a disciplined ghostwriter with 18+ years of experience "
                "turning spoken teachings into polished mini-book chapters. "
                "You generate the chapter, internally audit and refine it, "
                "and output ONLY the final chapter."
            )
        except Exception as e:
            logger.exception(f"Error loading system prompt: {e}")
            raise RuntimeError(f"Failed to load system prompt: {e}")

    def _load_user_prompt_template(self) -> str:
        """Load the user prompt template from file. Falls back to embedded default."""
        prompt_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "prompts", "conversion_prompt_user.txt"
        )
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                logger.info(f"Loaded user prompt template from {prompt_file}")
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"User prompt not found at {prompt_file}. Using embedded fallback.")
            return (
                "Transform the transcript below into a cohesive, self-contained "
                "mini-book chapter written in the teacher's voice.\n\n"
                "{main_speaker_instructions}\n\n"
                "{title_instruction}\n\n"
                "Transcript:\n{chat_text}"
            )
        except Exception as e:
            logger.exception(f"Error loading user prompt template: {e}")
            raise RuntimeError(f"Failed to load user prompt template: {e}")

    def _prepare_user_prompt(
        self, chat_text: str, main_speaker: Optional[str] = None, title: Optional[str] = None
    ) -> str:
        """
        Prepare the user prompt with content, speaker instructions, and title.

        Args:
            chat_text: The cleaned WhatsApp chat transcript.
            main_speaker: Optional name of the main teacher/speaker.
            title: Optional desired title for the article.

        Returns:
            The fully formatted user prompt string.
        """
        template = self._load_user_prompt_template()

        # Speaker instructions — no hardcoded phone numbers (privacy first)
        if main_speaker and main_speaker.strip():
            main_speaker_instructions = (
                f'The main teacher/speaker in this transcript is "{main_speaker}". '
                f"Focus primarily on their teachings, insights, and responses to questions. "
                f"Present their content as the authoritative voice, while incorporating "
                f"relevant questions and contributions from other participants only when "
                f"they enhance the teaching or provide necessary context."
            )
        else:
            main_speaker_instructions = (
                "Identify the main teacher/speaker from the content and focus on their "
                "teachings as the primary voice. If multiple speakers contribute significantly, "
                "blend their insights cohesively while maintaining a single authoritative "
                "teaching voice."
            )

        # Title instruction
        if title and title.strip():
            title_instruction = f'Use "{title}" as the chapter title and ensure the content aligns with this theme.'
        else:
            title_instruction = "Create an appropriate title that captures the main theme of the teaching."

        return template.format(
            main_speaker_instructions=main_speaker_instructions,
            chat_text=chat_text,
            title_instruction=title_instruction,
        )

    def convert_chat_to_article(
        self, chat_text: str, main_speaker: Optional[str] = None, title: Optional[str] = None
    ) -> str:
        """
        Converts chat text into an article using the Gemini LLM.

        Args:
            chat_text: The cleaned WhatsApp chat transcript.
            main_speaker: Optional name of the main teacher/speaker.
            title: Optional desired title for the article.

        Returns:
            The LLM-generated article text.

        Raises:
            ValueError: If no text is provided for conversion.
            RuntimeError: If the LLM conversion fails.
        """
        try:
            if not chat_text or not chat_text.strip():
                raise ValueError("No text provided for conversion")

            system_prompt = self._load_system_prompt()
            user_prompt = self._prepare_user_prompt(chat_text, main_speaker, title)
            logger.debug("Prompts prepared for LLM.")

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.model.invoke(messages)

            if not response or not response.content:
                logger.error("No content received from the LLM.")
                raise RuntimeError("No article content received from the AI model. Please try again.")

            logger.info("Successfully converted chat text to article.")
            return response.content.strip()

        except ValueError as ve:
            logger.error(f"Validation error during conversion: {ve}")
            raise
        except Exception as e:
            logger.exception(f"Error during LLM conversion: {e}")
            raise RuntimeError(f"Failed to convert text using Gemini: {e}")

    def test_connection(self) -> Tuple[bool, str]:
        """Tests the connection to the Gemini API."""
        try:
            response = self.model.invoke([
                HumanMessage(content="Hello, respond with only: Connection successful")
            ])
            if response and response.content and "connection successful" in response.content.lower():
                logger.info("Gemini API connection test: SUCCESS")
                return True, response.content.strip()
            msg = response.content if response and response.content else "Empty response"
            logger.warning(f"Gemini API connection test: Unexpected response: {msg}")
            return False, f"Unexpected response: {msg}"
        except Exception as e:
            logger.error(f"Gemini API connection test: FAILED - {e}")
            return False, str(e)

    def get_model_info(self) -> Dict[str, Any]:
        """Gets information about the current LLM configuration."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }
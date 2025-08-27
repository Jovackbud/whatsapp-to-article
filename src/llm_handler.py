import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage 
from .config import Config
import logging
from typing import Optional, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class GeminiHandler:
    """
    Handles interactions with the Google Gemini LLM using LangChain.
    Manages model initialization, prompt preparation, and text conversion.
    """
    
    def __init__(self):
        """Initializes the Gemini handler by validating config and setting up the LLM."""
        try:
            Config.validate_config() # This will raise ValueError if GOOGLE_API_KEY is missing
            self.model = ChatGoogleGenerativeAI(
                model=Config.GEMINI_MODEL,
                google_api_key=Config.GOOGLE_API_KEY,
                temperature=0.7,
                max_output_tokens=4096,
                verbose=False, # Set verbose to False by default for production
            )
            logger.info(f"Gemini model '{Config.GEMINI_MODEL}' initialized successfully.")
        except ValueError as ve:
            logger.error(f"Configuration error: {ve}")
            raise # Re-raise config validation errors
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini model: {e}")
            raise RuntimeError(f"Failed to initialize Gemini model. Please check your API key and model configuration. Error: {e}")
    
    def _load_prompt_template(self) -> str:
        """
        Load the prompt template from file with explicit Markdown heading instruction.
        Falls back to an embedded prompt if the file is not found.
        """
        # Construct path relative to the current file
        prompt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "conversion_prompt.txt")
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                logger.info(f"Loaded prompt template from {prompt_file}")
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Prompt file not found at {prompt_file}. Falling back to embedded prompt.")
            # Fallback to embedded prompt if file not found (update this with the _latest_ prompt from the .txt)
            return """You are an experienced writer with 15 years of experience turning class materials into "book type" writing - a kind of Ghost writer. I will give you a transcript of a WhatsApp class and you will synthesize the class teaching and the teacher's responses to students' (other participants') questions and contributions into a written format akin to an essay or mini-book chapter.

CRITICAL INSTRUCTIONS:
1. STICK TO WHAT IS IN THE PROVIDED CONTENT - DO NOT MAKE UP INFORMATION OR ADD YOUR INTERPRETATION OR ANY EXTERNAL KNOWLEDGE
2. Remove all emojis, datetime stamps, casual chat elements (greetings, "ok", "haha", etc.)
3. Do not make reference to other participants by name or as "students" - remember the readers were not in this class and did not know the class happened
4. This is NOT a report - it is a "mini-book" format where the content flows as if the teacher is speaking directly to the reader
5. Organize the content into logical sections with clear headings where appropriate. Use Markdown-style headings (e.g., "## Main Section Title", "### Sub-section Title") for easy formatting.
6. Use proper paragraph structure and smooth transitions
7. Write in a professional, engaging tone suitable for a book chapter
8. Maintain the teacher's voice and teaching style throughout
9. Structure the content with natural flow from introduction through main points to conclusion
10. Include relevant context and explanations that make the content self-contained

{main_speaker_instructions}

WRITING STYLE:
- Write as if the teacher is speaking directly to the reader in a book
- Use "I will start by saying..." "You see..." "Let me give an example..." type of natural teaching flow
- Maintain the conversational yet authoritative tone of a teacher
- Ensure the content reads as a cohesive chapter, not a transcribed conversation
- Remove any references to "this class", "today's lesson", or similar time-bound references
- Transform questions from participants into natural teaching moments without identifying the questioners

{title_instruction}

CONTENT TO CONVERT:
{chat_text}

Transform this WhatsApp class transcript into a well-formatted mini-book chapter that captures the teacher's wisdom and teachings in a format suitable for readers who want to learn from this content as if reading a book."""
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading prompt template: {e}")
            raise RuntimeError(f"Failed to load prompt template: {e}")

    def _prepare_prompt(self, chat_text: str, main_speaker: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        Prepare the complete prompt with content, main speaker instructions, and title instructions.
        
        Args:
            chat_text: The cleaned WhatsApp chat transcript.
            main_speaker: Optional name of the main teacher/speaker.
            title: Optional desired title for the article.
            
        Returns:
            The fully formatted prompt string.
        """
        template = self._load_prompt_template()
        
        # Prepare main speaker instructions
        if main_speaker and main_speaker.strip():
            main_speaker_instructions = f"""TEACHER IDENTIFICATION: The main teacher/speaker in this transcript is "{main_speaker}". Focus primarily on their teachings, insights, and responses to questions. Present their content as the authoritative voice throughout the chapter, while incorporating relevant questions and contributions from other participants only when they enhance the teaching or provide necessary context."""
        else:
            main_speaker_instructions = """TEACHER IDENTIFICATION: Identify the main teacher/speaker from the content and focus on their teachings as the primary voice. If multiple speakers contribute significantly, blend their insights cohesively while maintaining a single authoritative teaching voice."""
        
        # Prepare title instruction
        if title and title.strip():
            title_instruction = f"""CHAPTER TITLE: Use "{title}" as the chapter title and ensure the content aligns with this theme."""
        else:
            title_instruction = """CHAPTER TITLE: Create an appropriate title that captures the main theme of the teaching."""
        
        # Format the template
        formatted_prompt = template.format(
            main_speaker_instructions=main_speaker_instructions,
            chat_text=chat_text,
            title_instruction=title_instruction
        )
        
        return formatted_prompt

    def convert_chat_to_article(self, chat_text: str, main_speaker: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        Converts chat text into an article format using the Gemini LLM.
        
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

            # Prepare the complete prompt
            full_prompt = self._prepare_prompt(chat_text, main_speaker, title)
            logger.debug("Prompt prepared for LLM.")

            # Create message
            messages = [HumanMessage(content=full_prompt)]

            # Get response from model
            response = self.model.invoke(messages)
            
            if not response or not response.content:
                logger.error("No content received in the response from the LLM.")
                raise RuntimeError("No article content received from the AI model. Please try again.")

            logger.info("Successfully converted chat text to article.")
            return response.content.strip()

        except ValueError as ve:
            logger.error(f"Validation error during conversion: {ve}")
            raise # Re-raise ValueError
        except Exception as e:
            logger.exception(f"Error during LLM conversion: {e}")
            raise RuntimeError(f"Failed to convert text using Gemini: {e}. Please check your input and try again.")

    def test_connection(self) -> Tuple[bool, str]:
        """
        Tests the connection to the Gemini API.
        
        Returns:
            A tuple (success, message).
        """
        try:
            test_message = [HumanMessage(content="Hello, can you respond with 'Connection successful'?")]
            response = self.model.invoke(test_message)
            if "connection successful" in response.content.lower():
                logger.info("Gemini API connection test: SUCCESS")
                return True, response.content
            else:
                logger.warning(f"Gemini API connection test: FAILED - Unexpected response: {response.content}")
                return False, f"Unexpected response from API: {response.content}"
        except Exception as e:
            logger.error(f"Gemini API connection test: FAILED - {e}")
            return False, str(e)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Gets information about the current LLM configuration.
        
        Returns:
            A dictionary containing model details.
        """
        return {
            "model_name": self.model.model_name, # Use the actual model name from the initialized object
            "temperature": self.model.temperature,
            "max_output_tokens": self.model.max_output_tokens
        }
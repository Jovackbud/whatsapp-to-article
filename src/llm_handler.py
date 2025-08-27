import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from .config import Config

class GeminiHandler:
    """Handle Gemini LLM interactions"""
    
    def __init__(self):
        """Initialize the Gemini handler"""
        try:
            Config.validate_config()
            self.model = ChatGoogleGenerativeAI(
                model=Config.GEMINI_MODEL,
                google_api_key=Config.GOOGLE_API_KEY,
                temperature=0.7,
                max_output_tokens=4096,
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini model: {str(e)}")
    
    def _get_conversion_prompt(self, main_speaker=None):
        """Get the conversion prompt with optional main speaker context"""
        base_prompt = """You are an expert editor and writer. Convert the following chat conversation into a well-structured article or book chapter.

Instructions:
1. Focus on extracting meaningful content and insights from the conversation
2. Organize the information into logical sections with clear headings
3. Remove casual chat elements (greetings, "ok", "haha", etc.) 
4. Maintain key insights and information while making it readable
5. Use proper paragraph structure and smooth transitions
6. Create engaging subheadings to break up the content
7. Write in a professional, engaging tone suitable for an article or book chapter
8. Include relevant context from participants when it adds educational value
9. Structure the content with an introduction, main body sections, and conclusion
10. Ensure the article flows naturally and is engaging to read"""

        if main_speaker and main_speaker.strip():
            speaker_context = f"""
11. Pay special attention to content from "{main_speaker}" as they appear to be the main speaker/teacher
12. Organize the article around their key points and teachings
13. Use other participants' questions and comments to provide context and flow"""
            base_prompt += speaker_context

        return base_prompt

    def convert_chat_to_article(self, chat_text, main_speaker=None, title=None):
        """Convert chat text to article using Gemini"""
        try:
            if not chat_text or not chat_text.strip():
                raise ValueError("No text provided for conversion")

            # Prepare the prompt
            system_prompt = self._get_conversion_prompt(main_speaker)
            
            # Prepare the user message
            user_content = f"Chat Content to Convert:\n\n{chat_text}\n\n"
            if title:
                user_content += f"Suggested Title: {title}\n\n"
            user_content += "Please convert this chat into a well-formatted article:"

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ]

            # Get response from model
            response = self.model.invoke(messages)
            
            if not response or not response.content:
                raise Exception("No response received from the model")

            return response.content.strip()

        except Exception as e:
            raise Exception(f"Error converting text: {str(e)}")

    def test_connection(self):
        """Test the connection to Gemini API"""
        try:
            test_message = [HumanMessage(content="Hello, can you respond with 'Connection successful'?")]
            response = self.model.invoke(test_message)
            return True, response.content
        except Exception as e:
            return False, str(e)

    def get_model_info(self):
        """Get information about the current model"""
        return {
            "model_name": Config.GEMINI_MODEL,
            "temperature": 0.7,
            "max_tokens": 4096
        }
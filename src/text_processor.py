import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Provides static methods for cleaning, processing, and analyzing raw chat text.
    Removes irrelevant elements like timestamps, system messages, and casual chat.
    """
    
    @staticmethod
    def clean_chat_text(raw_text: str) -> str:
        """
        Cleans WhatsApp chat text by removing timestamps, system messages,
        and other non-content elements.
        
        Args:
            raw_text: The raw chat transcript string.
        
        Returns:
            The cleaned chat text.
        """
        if not raw_text:
            return ""
        
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        # Common WhatsApp patterns to remove
        whatsapp_patterns = [
            r'^\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}\s?[AP]?M?\s?-\s?',  # Timestamps
            r'^\[\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}:\d{2}\]\s?',       # Square bracket timestamps
            r'^Messages and calls are end-to-end encrypted.*',                  # Encryption notice
            r'^This message was deleted\.?$',                                   # Deleted messages
            r'^You deleted this message\.?$',                                   # Deleted messages
            r'^\s*<Media omitted>\s*$',                                        # Media omitted
            r'^\s*image omitted\s*$',                                          # Image omitted
            r'^\s*video omitted\s*$',                                          # Video omitted
            r'^\s*audio omitted\s*$',                                          # Audio omitted
            r'^\s*document omitted\s*$',                                       # Document omitted
            r'^\s*sticker omitted\s*$',                                        # Sticker omitted
            r'^\s*GIF omitted\s*$',                                            # GIF omitted
            r'.*added.*to the group$',                                         # Group additions
            r'.*left$',                                                        # Someone left
            r'.*changed the group description$',                               # Description changes
            r'.*changed the subject.*$',                                       # Subject changes
            r'^Missed voice call$',                                           # Missed calls
            r'^Missed video call$',                                           # Missed calls
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines matching WhatsApp patterns
            should_skip = False
            for pattern in whatsapp_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break
            
            if not should_skip:
                # Remove timestamp prefixes if any remain
                line = re.sub(r'^\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?\s?[AP]?M?\s?-\s?', '', line)
                line = re.sub(r'^\[\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}:\d{2}\]\s?', '', line)
                
                if line.strip():
                    cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def remove_casual_elements(text: str) -> str:
        """
        Removes casual chat elements (emojis, common slang, filler words)
        that are not relevant for an article.
        
        Args:
            text: The input text.
        
        Returns:
            The text with casual elements removed.
        """
        if not text:
            return ""
        
        # Combine all casual patterns into a single regex for efficiency
        casual_patterns = [
            r'\b(haha+|lol+|lmao+|omg+|okay?|ok\b|yeah+|yep+|nope+|hmm+|uhm+|um\b|ah\b|oh\b)\b', # Words
            r'[😂😄😊👍👌]+', # Emojis
            # Add any other common single-occurrence casual elements that might remain
        ]
        
        # Compile into a single regex pattern
        combined_pattern = re.compile('|'.join(casual_patterns), re.IGNORECASE)
        
        text = combined_pattern.sub('', text)
        
        # Clean up extra whitespace, including multiple newlines
        text = re.sub(r'\s+', ' ', text).strip() # Replace all whitespace with single space, then strip
        text = re.sub(r'\n\s*\n', '\n\n', text) # Ensure consistent paragraph breaks
        
        logger.debug("Casual elements removed from text.")
        return text.strip()
    
    @staticmethod
    def identify_speakers(text: str) -> List[str]:
        """Extract potential speaker names from chat text"""
        # This is a heuristic and might not catch all speaker patterns or misidentify some.
        if not text:
            return []
        
        # Pattern to match speaker names (name followed by colon)
        speaker_pattern = r'^([^:\n]+?):\s*(.+)$'
        speakers = set()
        
        for line in text.split('\n'):
            match = re.match(speaker_pattern, line.strip())
            if match:
                speaker_name = match.group(1).strip()
                # Filter out obvious non-names
                if (len(speaker_name) < 50 and 
                    not re.match(r'^\d', speaker_name) and  # Don't start with number
                    speaker_name not in ['Media', 'Image', 'Video', 'Audio', 'Document']):
                    speakers.add(speaker_name)
        
        return sorted(list(speakers))
    
    @staticmethod
    def prepare_for_conversion(text: str) -> str:
        """
        Prepares raw chat text for LLM conversion by applying cleaning and removal
        of casual elements.

        Args:
            text: The raw chat text.

        Returns:
            The processed text ready for LLM conversion.
        """
        if not text:
            logger.debug("No text provided for prepare_for_conversion, returning empty string.")
            return ""

        cleaned = TextProcessor.clean_chat_text(text)
        processed = TextProcessor.remove_casual_elements(cleaned)

        logger.info("Text prepared for LLM conversion.")
        return processed.strip()
    
    @staticmethod
    def format_output(article_text: str) -> str:
        """Format the LLM output for better readability"""
        if not article_text:
            return ""
        
        # Ensure proper paragraph spacing
        formatted = re.sub(r'\n{3,}', '\n\n', article_text)
        
        # Clean up any remaining formatting issues
        formatted = re.sub(r'[ \t]+', ' ', formatted)  # Multiple spaces to single
        formatted = formatted.strip()
        
        return formatted
    
    @staticmethod
    def get_text_stats(text: str) -> Dict[str, int]:
        """Get basic statistics about the text"""
        if not text:
            return {"words": 0, "characters": 0, "lines": 0}
        
        word_count = len(text.split())
        char_count = len(text)
        line_count = len([line for line in text.split('\n') if line.strip()])
        
        return {
            "words": word_count,
            "characters": char_count,
            "lines": line_count
        }
import re
from datetime import datetime

class TextProcessor:
    """Process and clean text for conversion"""
    
    @staticmethod
    def clean_chat_text(raw_text):
        """Clean WhatsApp chat text by removing timestamps and system messages"""
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
    def remove_casual_elements(text):
        """Remove casual chat elements like 'haha', 'ok', etc."""
        if not text:
            return ""
        
        # Patterns for casual elements
        casual_patterns = [
            r'\bhaha+\b',
            r'\blol+\b',
            r'\blmao+\b',
            r'\bomg+\b',
            r'\bokay?\b',
            r'\bok+\b(?!\w)',  # 'ok' but not part of another word
            r'\byeah+\b',
            r'\byep+\b',
            r'\bnope+\b',
            r'\bhmm+\b',
            r'\buhm+\b',
            r'\bum+\b(?!\w)',
            r'\bah+\b(?!\w)',
            r'\boh+\b(?!\w)',
            r'😂+',
            r'😄+',
            r'😊+',
            r'👍+',
            r'👌+',
        ]
        
        for pattern in casual_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    @staticmethod
    def identify_speakers(text):
        """Extract potential speaker names from chat text"""
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
    def prepare_for_conversion(text, main_speaker=None):
        """Prepare text for LLM conversion"""
        if not text:
            return ""
        
        # Clean the text
        cleaned = TextProcessor.clean_chat_text(text)
        
        # Remove casual elements
        processed = TextProcessor.remove_casual_elements(cleaned)
        
        # If main speaker is provided, highlight their contributions
        if main_speaker and main_speaker.strip():
            # This will be used in the prompt context
            pass
        
        return processed.strip()
    
    @staticmethod
    def format_output(article_text):
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
    def get_text_stats(text):
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
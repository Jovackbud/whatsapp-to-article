import streamlit as st
from docx import Document
import PyPDF2
import pdfplumber
from io import BytesIO
from .config import Config
import logging
from typing import Tuple, Any, List

logger = logging.getLogger(__name__)

class DocumentHandler:
    """
    Handles document upload, validation, and text extraction from various formats
    (TXT, DOCX, PDF).
    """
    
    @staticmethod
    def validate_file(uploaded_file: Any) -> Tuple[bool, str]:
        """
        Validate uploaded file type and size.
        
        Args:
            uploaded_file: The file object uploaded via Streamlit.
        
        Returns:
            A tuple (is_valid, message).
        """
        if uploaded_file is None:
            return False, "No file uploaded"
        
        # Check file extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in Config.SUPPORTED_FILE_TYPES:
            return False, f"Unsupported file type. Please upload: {', '.join(Config.SUPPORTED_FILE_TYPES)}"
        
        # Check file size
        if uploaded_file.size > Config.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        
        return True, "File is valid"
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """
        Extract text from TXT file.
        
        Args:
            file_content: The binary content of the TXT file.
            
        Returns:
            The extracted text.
            
        Raises:
            RuntimeError: If the file cannot be decoded.
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError("Unable to decode file with any supported encoding")
        except UnicodeDecodeError as ude:
            logger.error(f"Failed to decode TXT file with common encodings: {ude}")
            raise RuntimeError(f"Error reading TXT file: Unable to decode file. {ude}")
        except Exception as e:
            logger.exception(f"Unexpected error reading TXT file: {e}")
            raise RuntimeError(f"Error reading TXT file: {e}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_content: The binary content of the DOCX file.
            
        Returns:
            The extracted text.
            
        Raises:
            RuntimeError: If there's an error reading the DOCX file.
        """
        try:
            doc = Document(BytesIO(file_content))
            full_text: List[str] = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            logger.exception(f"Error reading DOCX file: {e}")
            raise RuntimeError(f"Error reading DOCX file: {e}")
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """
        Extract text from PDF file using pdfplumber (primary) and PyPDF2 (fallback).
        
        Args:
            file_content: The binary content of the PDF file.
            
        Returns:
            The extracted text.
            
        Raises:
            RuntimeError: If both PDF extraction methods fail.
        """
        try:
            text_content: List[str] = []
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            if not text_content:
                logger.warning("pdfplumber extracted no text, falling back to PyPDF2.")
                # Fallback to PyPDF2 if pdfplumber fails to extract any text
                return DocumentHandler._extract_text_pypdf2(file_content)
            
            return '\n'.join(text_content)
        except Exception as e:
            logger.warning(f"pdfplumber failed to extract text, falling back to PyPDF2. Error: {e}")
            try:
                return DocumentHandler._extract_text_pypdf2(file_content)
            except Exception as pypdf2_e:
                logger.exception(f"Both pdfplumber and PyPDF2 failed to extract text from PDF: {e} | {pypdf2_e}")
                raise RuntimeError(f"Error reading PDF file: Both extraction methods failed. {pypdf2_e}")
    
    @staticmethod
    def _extract_text_pypdf2(file_content: bytes) -> str:
        """
        Fallback PDF extraction using PyPDF2.
        
        Args:
            file_content: The binary content of the PDF file.
            
        Returns:
            The extracted text.
            
        Raises:
            RuntimeError: If there's an error reading the PDF file with PyPDF2.
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text_content: List[str] = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            return '\n'.join(text_content)
        except Exception as e:
            logger.exception(f"Error reading PDF file with PyPDF2: {e}")
            raise RuntimeError(f"Error reading PDF file with PyPDF2: {e}")
    
    @staticmethod
    def extract_text_from_file(uploaded_file: Any) -> str:
        """
        Main method to extract text from an uploaded file based on its type.
        
        Args:
            uploaded_file: The file object uploaded via Streamlit.
            
        Returns:
            The extracted and stripped text content.
            
        Raises:
            RuntimeError: If file validation or text extraction fails.
            Exception: For unexpected errors during the process.
        """
        try:
            # Validate file first
            is_valid, message = DocumentHandler.validate_file(uploaded_file)
            if not is_valid:
                logger.error(f"File validation failed: {message}")
                raise RuntimeError(message)
            
            # Get file content
            file_content = uploaded_file.read()
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Extract text based on file type
            if file_extension == 'txt':
                text = DocumentHandler.extract_text_from_txt(file_content)
            elif file_extension == 'docx':
                text = DocumentHandler.extract_text_from_docx(file_content)
            elif file_extension == 'pdf':
                text = DocumentHandler.extract_text_from_pdf(file_content)
            else:
                logger.error(f"Unsupported file type encountered after validation: {file_extension}")
                raise RuntimeError(f"Unsupported file type: {file_extension}")
            
            # Note: Warning about text length is now handled in app.py after extraction.
            return text.strip()
            
        except RuntimeError:
            raise # Re-raise known runtime errors
        except Exception as e:
            logger.exception(f"Failed to extract text from file: {e}")
            raise RuntimeError(f"Failed to extract text: {e}. Please check the file content.")
    
    @staticmethod
    def validate_text_input(text: str) -> Tuple[bool, str]:
        """
        Validate direct text input.
        
        Args:
            text: The raw text input string.
            
        Returns:
            A tuple (is_valid, message).
        """
        if not text or not text.strip():
            return False, "Please enter some text to convert"
        
        if len(text) > Config.MAX_TEXT_LENGTH:
            return False, f"Text too long. Maximum {Config.MAX_TEXT_LENGTH:,} characters allowed"
        
        return True, "Text is valid"
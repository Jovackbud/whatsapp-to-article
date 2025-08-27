import streamlit as st
from docx import Document
import PyPDF2
import pdfplumber
from io import BytesIO
from .config import Config

class DocumentHandler:
    """Handle document upload and text extraction"""
    
    @staticmethod
    def validate_file(uploaded_file):
        """Validate uploaded file type and size"""
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
    def extract_text_from_txt(file_content):
        """Extract text from TXT file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError("Unable to decode file with any supported encoding")
        except Exception as e:
            raise Exception(f"Error reading TXT file: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content):
        """Extract text from DOCX file"""
        try:
            doc = Document(BytesIO(file_content))
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            raise Exception(f"Error reading DOCX file: {str(e)}")
    
    @staticmethod
    def extract_text_from_pdf(file_content):
        """Extract text from PDF file using pdfplumber (more reliable)"""
        try:
            text_content = []
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            if not text_content:
                # Fallback to PyPDF2 if pdfplumber fails
                return DocumentHandler._extract_text_pypdf2(file_content)
            
            return '\n'.join(text_content)
        except Exception as e:
            # Fallback to PyPDF2
            try:
                return DocumentHandler._extract_text_pypdf2(file_content)
            except:
                raise Exception(f"Error reading PDF file: {str(e)}")
    
    @staticmethod
    def _extract_text_pypdf2(file_content):
        """Fallback PDF extraction using PyPDF2"""
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        text_content = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        return '\n'.join(text_content)
    
    @staticmethod
    def extract_text_from_file(uploaded_file):
        """Main method to extract text from uploaded file"""
        try:
            # Validate file first
            is_valid, message = DocumentHandler.validate_file(uploaded_file)
            if not is_valid:
                raise Exception(message)
            
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
                raise Exception(f"Unsupported file type: {file_extension}")
            
            # Validate text length
            if len(text) > Config.MAX_TEXT_LENGTH:
                st.warning(f"Text is very long ({len(text)} characters). Consider splitting into smaller parts for better results.")
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    @staticmethod
    def validate_text_input(text):
        """Validate direct text input"""
        if not text or not text.strip():
            return False, "Please enter some text to convert"
        
        if len(text) > Config.MAX_TEXT_LENGTH:
            return False, f"Text too long. Maximum {Config.MAX_TEXT_LENGTH:,} characters allowed"
        
        return True, "Text is valid"
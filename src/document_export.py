import streamlit as st
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from io import BytesIO
import pyperclip
from datetime import datetime
import re

class DocumentExporter:
    """Handle document export in various formats"""
    
    @staticmethod
    def create_word_doc(content, title=None, author="WhatsApp Chat Converter"):
        """Create a Word document from the content"""
        try:
            doc = Document()
            
            # Set document title
            if title:
                title_paragraph = doc.add_heading(title, 0)
                title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add metadata
            core_props = doc.core_properties
            core_props.author = author
            core_props.created = datetime.now()
            
            # Split content into paragraphs and headings
            lines = content.split('\n')
            current_paragraph = ""
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    if current_paragraph:
                        doc.add_paragraph(current_paragraph)
                        current_paragraph = ""
                    continue
                
                # Detect headings (lines that are short and might be headings)
                if DocumentExporter._is_heading(line):
                    # Add previous paragraph if exists
                    if current_paragraph:
                        doc.add_paragraph(current_paragraph)
                        current_paragraph = ""
                    
                    # Determine heading level
                    if line.isupper() or line.startswith('#'):
                        heading_level = 1
                    elif any(word in line.lower() for word in ['introduction', 'conclusion', 'overview', 'summary']):
                        heading_level = 1  
                    else:
                        heading_level = 2
                    
                    # Clean heading text
                    clean_heading = line.replace('#', '').strip()
                    doc.add_heading(clean_heading, heading_level)
                else:
                    # Regular content
                    if current_paragraph:
                        current_paragraph += " " + line
                    else:
                        current_paragraph = line
            
            # Add final paragraph if exists
            if current_paragraph:
                doc.add_paragraph(current_paragraph)
            
            # Save to BytesIO
            doc_buffer = BytesIO()
            doc.save(doc_buffer)
            doc_buffer.seek(0)
            
            return doc_buffer.getvalue()
            
        except Exception as e:
            raise Exception(f"Error creating Word document: {str(e)}")
    
    @staticmethod
    def create_pdf(content, title=None, author="WhatsApp Chat Converter"):
        """Create a PDF document from the content"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor='#2E4053'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=12,
                textColor='#34495E'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6,
                leftIndent=0,
                rightIndent=0
            )
            
            # Build the document
            story = []
            
            # Add title if provided
            if title:
                story.append(Paragraph(title, title_style))
                story.append(Spacer(1, 20))
            
            # Process content
            lines = content.split('\n')
            current_paragraph = ""
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    if current_paragraph:
                        story.append(Paragraph(current_paragraph, body_style))
                        current_paragraph = ""
                    continue
                
                if DocumentExporter._is_heading(line):
                    # Add previous paragraph if exists
                    if current_paragraph:
                        story.append(Paragraph(current_paragraph, body_style))
                        current_paragraph = ""
                    
                    # Add heading
                    clean_heading = line.replace('#', '').strip()
                    story.append(Paragraph(clean_heading, heading_style))
                else:
                    # Accumulate paragraph content
                    if current_paragraph:
                        current_paragraph += " " + line
                    else:
                        current_paragraph = line
            
            # Add final paragraph if exists
            if current_paragraph:
                story.append(Paragraph(current_paragraph, body_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            raise Exception(f"Error creating PDF document: {str(e)}")
    
    @staticmethod
    def copy_to_clipboard(content):
        """Copy content to clipboard"""
        try:
            pyperclip.copy(content)
            return True, "Content copied to clipboard successfully!"
        except Exception as e:
            return False, f"Failed to copy to clipboard: {str(e)}"
    
    @staticmethod
    def _is_heading(line):
        """Determine if a line should be treated as a heading"""
        if not line or len(line) < 3:
            return False
        
        # Check for explicit heading markers
        if line.startswith('#') or line.startswith('##'):
            return True
        
        # Check for common heading patterns
        heading_indicators = [
            'introduction', 'conclusion', 'overview', 'summary', 
            'background', 'discussion', 'analysis', 'findings',
            'key points', 'main ideas', 'important notes'
        ]
        
        line_lower = line.lower()
        for indicator in heading_indicators:
            if indicator in line_lower:
                return True
        
        # Check if line is short and might be a heading
        if len(line) < 60 and ':' not in line and line.endswith(('.', ':', '!')):
            return True
        
        # Check if line is all caps (but not too long)
        if line.isupper() and len(line) < 80:
            return True
        
        return False
    
    @staticmethod
    def generate_filename(title=None, file_type="docx"):
        """Generate a filename for download"""
        if title:
            # Clean title for filename
            clean_title = re.sub(r'[^\w\s-]', '', title)
            clean_title = re.sub(r'[-\s]+', '-', clean_title)
            filename = f"{clean_title}.{file_type}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"converted_article_{timestamp}.{file_type}"
        
        return filename
    
    @staticmethod
    def get_download_button_html(content, filename, button_text, button_key):
        """Generate HTML for download button (fallback method)"""
        import base64
        
        if filename.endswith('.docx'):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.endswith('.pdf'):
            mime_type = "application/pdf"
        else:
            mime_type = "text/plain"
        
        b64_content = base64.b64encode(content).decode()
        
        download_link = f'''
        <a href="data:{mime_type};base64,{b64_content}" 
           download="{filename}" 
           style="text-decoration: none;">
            <button style="
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            ">
                {button_text}
            </button>
        </a>
        '''
        return download_link
import streamlit as st
import time
import traceback
from src.config import Config
from src.document_handler import DocumentHandler
from src.text_processor import TextProcessor
from src.llm_handler import GeminiHandler
from src.document_export import DocumentExporter

# Page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_app():
    """Initialize the application and check configuration"""
    try:
        Config.validate_config()
        return True, None
    except Exception as e:
        return False, str(e)

def display_header():
    """Display the application header"""
    st.title("📝 WhatsApp to Article Converter")
    st.markdown("""
    Convert your WhatsApp chat exports into well-structured articles or book chapters. 
    Simply upload a file or paste your text, and let AI transform it into readable content.
    """)
    st.divider()

def display_input_section():
    """Display the input section"""
    st.subheader("📄 Input Your Content")
    
    # Create two columns for input methods
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Option 1: Upload a File**")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=Config.SUPPORTED_FILE_TYPES,
            help=f"Supported formats: {', '.join(Config.SUPPORTED_FILE_TYPES).upper()}"
        )
    
    with col2:
        st.markdown("**Option 2: Paste Text Directly**")
        direct_text = st.text_area(
            "Paste your chat text here",
            height=150,
            placeholder="Paste your WhatsApp chat export or any text you want to convert...",
            help="You can paste text directly instead of uploading a file"
        )
    
    # Main speaker input (full width)
    st.markdown("**Main Speaker/Teacher (Optional)**")
    main_speaker = st.text_input(
        "Who was the main speaker or teacher in this conversation?",
        placeholder="e.g., Dr. Smith, John Doe, Teacher Name...",
        help="If specified, the AI will focus on this person's contributions as the primary content"
    )
    
    return uploaded_file, direct_text, main_speaker

def process_input(uploaded_file, direct_text):
    """Process the input and extract text"""
    try:
        text_content = ""
        source_type = ""
        
        if uploaded_file is not None:
            # Process uploaded file
            with st.spinner("Extracting text from file..."):
                text_content = DocumentHandler.extract_text_from_file(uploaded_file)
                source_type = f"file ({uploaded_file.name})"
        elif direct_text and direct_text.strip():
            # Process direct text input
            is_valid, message = DocumentHandler.validate_text_input(direct_text)
            if not is_valid:
                st.error(message)
                return None, None
            text_content = direct_text.strip()
            source_type = "direct input"
        else:
            st.warning("Please either upload a file or enter text directly.")
            return None, None
        
        return text_content, source_type
        
    except Exception as e:
        st.error(f"Error processing input: {str(e)}")
        return None, None

def display_processing_section(text_content, source_type, main_speaker):
    """Display the processing section"""
    if not text_content:
        return None
    
    st.subheader("🔄 Processing")
    
    # Show text statistics
    stats = TextProcessor.get_text_stats(text_content)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Source", source_type)
    with col2:
        st.metric("Words", f"{stats['words']:,}")
    with col3:
        st.metric("Characters", f"{stats['characters']:,}")
    with col4:
        st.metric("Lines", f"{stats['lines']:,}")
    
    # Processing options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        article_title = st.text_input(
            "Article Title (Optional)",
            placeholder="Enter a title for your article...",
            help="This will be used as the title in exported documents"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        convert_button = st.button(
            "🚀 Convert to Article",
            type="primary",
            use_container_width=True
        )
    
    if convert_button:
        return convert_text_to_article(text_content, main_speaker, article_title)
    
    return None

def convert_text_to_article(text_content, main_speaker, article_title):
    """Convert text to article using AI"""
    try:
        with st.spinner("Converting to article... This may take a moment."):
            # Initialize LLM handler
            llm_handler = GeminiHandler()
            
            # Preprocess the text
            processed_text = TextProcessor.prepare_for_conversion(text_content, main_speaker)
            
            if not processed_text:
                st.error("No meaningful content found after processing. Please check your input.")
                return None
            
            # Convert to article
            start_time = time.time()
            article_content = llm_handler.convert_chat_to_article(
                processed_text, 
                main_speaker, 
                article_title
            )
            processing_time = time.time() - start_time
            
            # Format the output
            formatted_article = TextProcessor.format_output(article_content)
            
            if formatted_article:
                st.success(f"✅ Conversion completed in {processing_time:.1f} seconds!")
                return formatted_article, article_title, processing_time
            else:
                st.error("Conversion failed - no content generated.")
                return None
                
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")
        if st.checkbox("Show detailed error (for debugging)"):
            st.code(traceback.format_exc())
        return None

def display_output_section(article_content, article_title, processing_time):
    """Display the output section with export options"""
    if not article_content:
        return
    
    st.subheader("📝 Generated Article")
    
    # Show output statistics
    output_stats = TextProcessor.get_text_stats(article_content)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Words", f"{output_stats['words']:,}")
    with col2:
        st.metric("Characters", f"{output_stats['characters']:,}")
    with col3:
        st.metric("Paragraphs", f"{output_stats['lines']:,}")
    with col4:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    # Display the article content
    with st.container():
        st.markdown("### Preview")
        st.markdown(article_content)
    
    st.divider()
    
    # Export options
    st.subheader("📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    # Copy to clipboard
    with col1:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            success, message = DocumentExporter.copy_to_clipboard(article_content)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Download as Word document
    with col2:
        try:
            docx_content = DocumentExporter.create_word_doc(
                article_content, 
                article_title or Config.DEFAULT_TITLE
            )
            filename_docx = DocumentExporter.generate_filename(article_title, "docx")
            
            st.download_button(
                label="📝 Download DOCX",
                data=docx_content,
                file_name=filename_docx,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error creating DOCX: {str(e)}")
    
    # Download as PDF
    with col3:
        try:
            pdf_content = DocumentExporter.create_pdf(
                article_content, 
                article_title or Config.DEFAULT_TITLE
            )
            filename_pdf = DocumentExporter.generate_filename(article_title, "pdf")
            
            st.download_button(
                label="📄 Download PDF",
                data=pdf_content,
                file_name=filename_pdf,
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error creating PDF: {str(e)}")

def display_sidebar():
    """Display the sidebar with information and settings"""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This tool converts WhatsApp chat exports into readable articles using AI.
        
        **Supported Input:**
        - TXT files (WhatsApp exports)
        - DOCX documents
        - PDF files
        - Direct text input
        
        **Features:**
        - Automatic chat cleaning
        - Speaker identification
        - Multiple export formats
        - Professional formatting
        """)
        
        st.divider()
        
        st.header("💡 Tips")
        st.markdown("""
        - **Better Results:** Specify the main speaker/teacher
        - **File Size:** Keep files under 10MB
        - **Quality:** Longer conversations work better
        - **Privacy:** All processing is secure
        """)
        
        st.divider()
        
        # Model information (for developers)
        if st.checkbox("Show Model Info", help="Developer information"):
            try:
                llm_handler = GeminiHandler()
                model_info = llm_handler.get_model_info()
                st.json(model_info)
            except Exception as e:
                st.error(f"Model info unavailable: {str(e)}")

def main():
    """Main application function"""
    # Initialize app
    is_initialized, error_message = initialize_app()
    
    if not is_initialized:
        st.error(f"❌ Configuration Error: {error_message}")
        st.info("Please check your environment variables and API keys.")
        st.stop()
    
    # Display sidebar
    display_sidebar()
    
    # Display main interface
    display_header()
    
    # Input section
    uploaded_file, direct_text, main_speaker = display_input_section()
    
    # Process input if available
    text_content, source_type = process_input(uploaded_file, direct_text)
    
    if text_content:
        # Show preview of input
        with st.expander("📖 Preview Input Text", expanded=False):
            preview_text = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
            st.text_area("Input Preview", preview_text, height=200, disabled=True)
        
        # Processing section
        result = display_processing_section(text_content, source_type, main_speaker)
        
        if result:
            article_content, article_title, processing_time = result
            display_output_section(article_content, article_title, processing_time)

if __name__ == "__main__":
    main()
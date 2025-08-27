import streamlit as st
import time
import traceback
import logging
import os
from typing import Optional, Tuple, Any

from src.config import Config
from src.document_handler import DocumentHandler
from src.text_processor import TextProcessor
from src.llm_handler import GeminiHandler
from src.document_export import DocumentExporter

# --- Logging Configuration ---
# Set a default logging level from environment variable or INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# -----------------------------

# Page configuration
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource(ttl=3600) # Cache for 1 hour to handle long sessions, adjust as needed
def get_gemini_handler() -> GeminiHandler:
    """
    Initializes and caches the GeminiHandler.
    This resource will be cached to prevent re-initialization on every Streamlit rerun.
    """
    try:
        handler = GeminiHandler()
        logger.info("GeminiHandler initialized and cached.")
        return handler
    except Exception as e:
        logger.critical(f"Failed to initialize GeminiHandler: {e}")
        st.error(f"Critical Error: Could not initialize AI model. Please check your API key and configuration. Details: {e}")
        st.stop() # Stop the app if LLM cannot be initialized

def initialize_app() -> Tuple[bool, Optional[str]]:
    """
    Initialize the application by validating configuration.
    The GeminiHandler is now cached and initialized separately by get_gemini_handler().
    """
    try:
        Config.validate_config()
        # Attempt to get the handler to ensure it's initialized on first run
        get_gemini_handler() 
        logger.info("Application configuration validated successfully.")
        return True, None
    except ValueError as e: # Catch specific config errors
        logger.error(f"Configuration validation failed: {e}")
        return False, str(e)
    except Exception as e:
        logger.exception(f"An unexpected error occurred during app initialization: {e}")
        return False, f"An unexpected error occurred during initialization: {e}"

def display_header() -> None:
    """Displays the main header and introduction of the application."""
    st.title("📝 WhatsApp to Article Converter")
    st.markdown("""
    Convert your WhatsApp chat exports into well-structured articles or book chapters. 
    Simply upload a file or paste your text, and let AI transform it into readable content.
    """)
    st.divider()

def display_input_section() -> Tuple[Any, str, str]:
    """
    Displays the input section allowing users to upload a file or paste text.
    
    Returns:
        A tuple containing:
        - uploaded_file: The Streamlit uploaded file object.
        - direct_text: The string content from the text area.
        - main_speaker: The string input for the main speaker.
    """
    st.subheader("📄 Input Your Content")
    
    # Create two columns for input methods
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Option 1: Upload a File**")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=list(Config.SUPPORTED_FILE_TYPES), # Convert frozenset to list for st.file_uploader
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

def process_input(uploaded_file: Any, direct_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Processes the input from either an uploaded file or direct text.
    
    Args:
        uploaded_file: The Streamlit uploaded file object.
        direct_text: The string content from the text area.
        
    Returns:
        A tuple (text_content, source_type) or (None, None) if processing fails or no input.
    """
    try:
        text_content: Optional[str] = None
        source_type: Optional[str] = None
        
        if uploaded_file is not None:
            # Process uploaded file
            with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                text_content = DocumentHandler.extract_text_from_file(uploaded_file)
                source_type = f"file ({uploaded_file.name})"
                logger.info(f"Text extracted from {uploaded_file.name}.")
        elif direct_text and direct_text.strip():
            # Process direct text input
            is_valid, message = DocumentHandler.validate_text_input(direct_text)
            if not is_valid:
                st.error(f"Input text validation failed: {message}")
                return None, None
            text_content = direct_text.strip()
            source_type = "direct input"
            logger.info("Direct text input processed.")
        else:
            st.warning("Please either upload a file or paste your chat text to proceed.")
            return None, None
        
        # Check for length after extraction/input
        if text_content and len(text_content) > Config.MAX_TEXT_LENGTH:
            st.warning(f"The input text is very long ({len(text_content):,} characters). "
                       f"The AI model may struggle with very long inputs, or results might be truncated. "
                       f"Consider using shorter chat exports for better results (max {Config.MAX_TEXT_LENGTH:,} characters).")
        
        return text_content, source_type
        
    except RuntimeError as re: # Catch specific errors from DocumentHandler
        st.error(f"Failed to process input: {re}. Please try a different file or text.")
        logger.error(f"Runtime error during input processing: {re}")
        return None, None
    except Exception as e:
        st.error(f"An unexpected error occurred while processing input: {e}")
        logger.exception(f"Unexpected error in process_input: {e}")
        return None, None

def display_processing_section(text_content: str, source_type: str, main_speaker: str) -> None:
    """
    Displays the processing section, including text statistics and conversion button.
    Triggers the LLM conversion and stores results in session state upon button click.
    """
    if not text_content:
        return
    
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
            help="This will be used as the title in exported documents",
            key="article_title_input" # Add a key to avoid duplicate widget error
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        convert_button = st.button(
            "🚀 Convert to Article",
            type="primary",
            use_container_width=True
        )
    
    if convert_button:
        # Trigger conversion and store results in session state
        success = convert_text_to_article(text_content, main_speaker, article_title)
        if success:
            st.rerun() # Force a rerun to display the output section immediately

def convert_text_to_article(text_content: str, main_speaker: str, article_title: str) -> bool:
    """
    Converts text to an article using AI and stores the result in Streamlit's session state.
    
    Args:
        text_content: The raw or pre-processed chat text.
        main_speaker: The identified main speaker/teacher.
        article_title: The desired title for the article.
        
    Returns:
        True if conversion was successful, False otherwise.
    """
    try:
        with st.spinner("Converting to article... This may take a moment."):
            # Get cached LLM handler
            llm_handler = get_gemini_handler()
            
            # Preprocess the text
            processed_text = TextProcessor.prepare_for_conversion(text_content)
            
            if not processed_text:
                st.error("No meaningful content found after processing. Please check your input.")
                logger.warning("Processed text was empty, conversion halted.")
                return False
            
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
                st.session_state.article_content = formatted_article
                st.session_state.article_title = article_title
                st.session_state.processing_time = processing_time
                logger.info(f"Conversion completed in {processing_time:.1f} seconds. Article generated.")
                return True
            else:
                st.error("Conversion failed - no content generated by the AI model.")
                logger.error("AI model returned no content for the article.")
                return False
                
    except RuntimeError as re:
        st.error(f"Conversion failed: {re}")
        logger.error(f"Runtime error during conversion: {re}")
        if st.checkbox("Show detailed error (for debugging)", key="debug_llm_error"):
            st.code(traceback.format_exc())
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during conversion: {e}")
        logger.exception(f"Unexpected error in convert_text_to_article: {e}")
        if st.checkbox("Show detailed error (for debugging)", key="debug_conversion_error"):
            st.code(traceback.format_exc())
        return False

def display_output_section(article_content: str, article_title: Optional[str], processing_time: float) -> None:
    """
    Displays the generated article content along with export options.
    
    Args:
        article_content: The LLM-generated article text.
        article_title: The title of the article (can be None).
        processing_time: The time taken for conversion.
    """
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
    
    # Display the article content in a text area for easy copying
    st.markdown("### Preview")
    st.text_area(
        "Read and Copy your Generated Article Here:",
        value=article_content,
        height=400,
        disabled=False, # Make it editable/copyable
        key="generated_article_preview"
    )
    st.info("To copy the article, click inside the box above, then use Ctrl+A (Cmd+A) to select all and Ctrl+C (Cmd+C) to copy.")
    
    st.divider()
    
    # Export options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2) # Reduced to two columns as direct copy is handled above
    
    # Download as Word document
    with col1:
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
                use_container_width=True,
                key="download_docx_button"
            )
        except Exception as e:
            logger.error(f"Error creating DOCX: {e}")
            st.error(f"Failed to create Word document. Please try again or report this issue.")
    
    # Download as PDF
    with col2:
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
                use_container_width=True,
                key="download_pdf_button"
            )
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            st.error(f"Failed to create PDF document. Please try again or report this issue.")

def display_sidebar() -> None:
    """Displays the sidebar with information and settings."""
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
        if st.checkbox("Show Model Info", help="Developer information", key="show_model_info_checkbox"):
            try:
                llm_handler = get_gemini_handler() # Get cached handler
                model_info = llm_handler.get_model_info()
                st.json(model_info)
            except Exception as e:
                # Use warning here, as it might be a temporary issue after initial error
                st.warning(f"Model info temporarily unavailable: {str(e)}")
                logger.warning(f"Failed to retrieve model info: {e}")

def main() -> None:
    """Main application function orchestrating the Streamlit UI and logic."""
    # Initialize app
    is_initialized, error_message = initialize_app()
    
    if not is_initialized:
        st.error(f"❌ Configuration Error: {error_message}")
        st.info("Please check your environment variables and API keys.")
        st.stop()
    
    # Initialize session state for storing results
    if 'article_content' not in st.session_state:
        st.session_state.article_content = None
    if 'article_title' not in st.session_state:
        st.session_state.article_title = None
    if 'processing_time' not in st.session_state:
        st.session_state.processing_time = None
    if 'last_input_hash' not in st.session_state:
        st.session_state.last_input_hash = None

    # Display sidebar
    display_sidebar()
    
    # Display main interface
    display_header()
    
    # Input section
    uploaded_file, direct_text, main_speaker = display_input_section()

    # Generate a hash for the current input combination
    current_input_hash = hash((uploaded_file.name if uploaded_file else None, direct_text, main_speaker))

    # Check if new input is provided and clear previous results if any
    if current_input_hash != st.session_state.last_input_hash:
        # Only clear and rerun if there was previous output or it's not the initial load
        if st.session_state.article_content is not None or st.session_state.last_input_hash is not None:
            st.session_state.article_content = None
            st.session_state.article_title = None
            st.session_state.processing_time = None
            logger.info("New input detected, clearing previous results and rerunning.")
            # Update hash immediately before rerun to avoid infinite loop
            st.session_state.last_input_hash = current_input_hash
            st.rerun() 
        else:
            # First load or no previous input, just update hash
            st.session_state.last_input_hash = current_input_hash

    # Process input if available
    text_content, source_type = process_input(uploaded_file, direct_text)
    
    if text_content:
        # Show preview of input
        with st.expander("📖 Preview Input Text", expanded=False):
            preview_text = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
            st.text_area("Input Preview", preview_text, height=200, disabled=True, key="input_preview_area")
        
        # Processing section
        display_processing_section(text_content, source_type, main_speaker)
        
    # Display output section if content is in session state (either from current run or previous rerun)
    if st.session_state.article_content:
        display_output_section(
            st.session_state.article_content,
            st.session_state.article_title,
            st.session_state.processing_time
        )

if __name__ == "__main__":
    main()
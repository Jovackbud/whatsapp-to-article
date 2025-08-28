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
    initial_sidebar_state="auto" # Auto-expand sidebar on wider screens
)

def set_custom_css():
    """Injects custom CSS for improved styling and responsiveness, reducing vertical space."""
    primary_color = st.get_option('theme.primaryColor')
    text_color = st.get_option('theme.textColor')
    secondary_background_color = st.get_option('theme.secondaryBackgroundColor')

    st.markdown(
        f"""
        <style>
            /* General Body Styling */
            html, body, [data-testid="stAppViewContainer"] {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}

            /* Main content area padding and centering for better readability */
            .stApp > header {{
                background-color: transparent;
            }}
            .stApp {{
                max-width: 1000px; /* Slightly reduced max width for compactness */
                margin: 0 auto; /* Center content on large screens */
                padding-top: 1rem; /* Reduced top padding */
                padding-bottom: 1rem; /* Reduced bottom padding */
            }}

            /* Streamlit Title (H1) */
            .title-font {{
                font-size: 36px; /* Slightly smaller H1 */
                color: {primary_color};
                margin-top: 0; /* Reduced top margin */
                margin-bottom: 0.5rem; /* Reduced bottom margin */
            }}
            
            /* Streamlit Subheaders (H2 - Section Headers) */
            h2 {{
                color: {primary_color};
                border-bottom: 1px solid #DDD; /* Lighter border */
                padding-bottom: 0.4rem; /* Reduced padding */
                margin-top: 1.5rem; /* Reduced top margin */
                margin-bottom: 0.8rem; /* Reduced bottom margin */
                font-size: 24px; /* Slightly smaller H2 */
            }}

            /* H3 Headings */
            h3 {{
                color: #444; /* Slightly darker than default to stand out */
                margin-top: 1.2rem; /* Reduced top margin */
                margin-bottom: 0.6rem; /* Reduced bottom margin */
                font-size: 20px; /* Slightly smaller H3 */
            }}

            /* H4 Headings */
            h4 {{
                font-size: 18px; /* Slightly smaller H4 */
                margin-top: 1rem;
                margin-bottom: 0.5rem;
            }}

            /* Metrics for better alignment and spacing */
            [data-testid="stMetricValue"] {{
                font-size: 1.6rem; /* Slightly smaller metric values */
                color: #333;
            }}
            [data-testid="stMetricLabel"] {{
                font-size: 0.85rem; /* Slightly smaller metric labels */
                color: #666;
            }}

            /* Text areas for better readability */
            .stTextArea > label {{
                font-weight: bold;
                color: {text_color};
                margin-bottom: 0.2rem; /* Reduced margin below label */
            }}
            .stTextArea textarea {{
                font-family: monospace; /* Good for code/text copy */
                font-size: 0.9em; /* Slightly smaller text in text areas */
                line-height: 1.5;
            }}

            /* Download buttons - ensure consistency */
            .stDownloadButton button {{
                background-color: {primary_color} !important;
                color: white !important;
                border-radius: 8px;
                border: none;
                padding: 8px 16px; /* Slightly reduced padding */
                font-size: 0.95rem; /* Slightly smaller font */
                transition: all 0.2s ease-in-out;
            }}
            .stDownloadButton button:hover {{
                background-color: #3e8e41 !important; /* Slightly darker green on hover */
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}

            /* Main Primary Button (Convert) */
            .stButton button.primary {{
                background-color: {primary_color};
                color: white;
                border-radius: 12px;
                font-size: 1.1rem; /* Slightly smaller primary button font */
                padding: 10px 20px; /* Slightly reduced padding */
                transition: all 0.2s ease-in-out;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }}
            .stButton button.primary:hover {{
                background-color: #3e8e41; /* Slightly darker green on hover */
                transform: translateY(-3px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.25);
            }}

            /* Info, Warning, Error boxes */
            [data-testid="stAlert"] {{
                margin-top: 0.8rem; /* Reduced margin */
                margin-bottom: 0.8rem; /* Reduced margin */
                border-radius: 8px;
                padding: 0.8rem; /* Reduced padding */
                font-size: 0.9em; /* Slightly smaller font in alerts */
            }}

            /* Expander titles */
            .streamlit-expanderHeader {{
                font-weight: bold;
                color: {primary_color};
                padding-top: 0.5rem; /* Reduced padding */
                padding-bottom: 0.5rem; /* Reduced padding */
                font-size: 1rem; /* Adjust expander title font size */
            }}
            
            /* Streamlit Divider - custom vertical space */
            .st-emotion-cache-16p6i0i {{ /* Target the divider element by its class/data-testid */
                margin-top: 0.5rem !important; /* Reduced margin */
                margin-bottom: 0.5rem !important; /* Reduced margin */
            }}

            /* Adjust spacing for columns - ensure they don't break on small screens */
            .st-emotion-cache-jgy9pp {{ /* Target for column content padding */
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }}
            
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the CSS function immediately after page config
set_custom_css()


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
    st.markdown(
        f"""
        <style>
        .title-font {{
            font-size: 36px; /* Adjusted H1 size */
            color: {st.get_option('theme.primaryColor')};
            margin-top: 0;
            margin-bottom: 0.5rem; /* Reduced margin */
        }}
        </style>
        <h1 class="title-font">📝 WhatsApp to Article Converter</h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
    Transform your raw WhatsApp chat transcripts into polished articles or book chapters. 
    This AI-powered tool extracts the core teachings and discussions, then formats them for professional readability.
    """)
    st.info("💡 **Tip:** For best results, ensure your chat export contains substantial teaching content and consider specifying the main speaker.")
    st.divider() # Uses custom CSS for reduced margin

def display_input_section() -> Tuple[Any, str, str]:
    """
    Displays the input section allowing users to upload a file or paste text.
    
    Returns:
        A tuple containing:
        - uploaded_file: The Streamlit uploaded file object.
        - direct_text: The string content from the text area.
        - main_speaker: The string input for the main speaker.
    """
    st.subheader("1. 📥 Provide Your Content")
    
    # Initialize session state for input elements if not present
    if 'file_uploader_value' not in st.session_state:
        st.session_state.file_uploader_value = None
    if 'direct_text_input_value' not in st.session_state:
        st.session_state.direct_text_input_value = ""
    if 'main_speaker_input_value' not in st.session_state:
        st.session_state.main_speaker_input_value = ""
    if 'article_title_input_value' not in st.session_state:
        st.session_state.article_title_input_value = ""

    col1, col2 = st.columns(2)
    current_uploaded_file = None 
    current_direct_text = ""
    
    with col1:
        st.markdown("##### **Option A: Upload Chat File**")
        uploaded_file_widget = st.file_uploader(
            "Upload TXT, DOCX, or PDF",
            type=list(Config.SUPPORTED_FILE_TYPES),
            help=f"Supported formats: {', '.join(Config.SUPPORTED_FILE_TYPES).upper()}. Max {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB.",
            key="file_uploader",
            on_change=lambda: st.session_state.__setitem__('file_uploader_value', st.session_state.file_uploader)
        )
        current_uploaded_file = st.session_state.file_uploader_value

    with col2:
        st.markdown("##### **Option B: Paste Text Directly**")
        direct_text_widget = st.text_area(
            "Paste Chat Transcript Here",
            height=180,
            placeholder="Paste your WhatsApp chat export (or any text) that you want to convert...",
            help=f"You can paste text directly. Maximum {Config.MAX_TEXT_LENGTH:,} characters.",
            key="direct_text_input",
            value=st.session_state.direct_text_input_value, 
            on_change=lambda: st.session_state.__setitem__('direct_text_input_value', st.session_state.direct_text_input)
        )
        current_direct_text = st.session_state.direct_text_input_value

    st.divider() # Replaced st.markdown("---") for consistent styling

    st.subheader("2. 🧑‍🏫 Identify Main Speaker (Optional)")
    main_speaker_widget = st.text_input(
        "Enter the name of the main teacher/speaker:",
        placeholder="e.g., Prof. Anya, Coach Ben, My Mentor...",
        help="Providing the speaker's name helps the AI maintain their voice and focus on their key teachings.",
        key="main_speaker_input",
        value=st.session_state.main_speaker_input_value, 
        on_change=lambda: st.session_state.__setitem__('main_speaker_input_value', st.session_state.main_speaker_input)
    )

    # Clear Inputs Button
    # st.markdown("<br>") # Removed extra spacing
    if st.button("🗑️ Clear All Inputs", help="Clear uploaded file, text, speaker name, and any generated article.", key="clear_inputs_button"):
        st.session_state.file_uploader_value = None 
        # Note: Streamlit does not support programmatically clearing the file_uploader widget.
        st.session_state.direct_text_input_value = ""
        st.session_state.main_speaker_input_value = ""
        st.session_state.article_title_input_value = ""
        st.session_state.article_content = None 
        st.session_state.article_title = None
        st.session_state.processing_time = None
        st.session_state.last_input_hash = None 
        logger.info("User cleared all inputs via button.")
        st.rerun() 

    st.divider() # Replaced st.markdown("---") for consistent styling

    current_main_speaker = st.session_state.main_speaker_input_value

    return current_uploaded_file, current_direct_text, current_main_speaker

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
            with st.spinner(f"Extracting text from {uploaded_file.name}..."):
                text_content = DocumentHandler.extract_text_from_file(uploaded_file)
                source_type = f"file ({uploaded_file.name})"
                logger.info(f"Text extracted from {uploaded_file.name}.")
        elif direct_text and direct_text.strip():
            is_valid, message = DocumentHandler.validate_text_input(direct_text)
            if not is_valid:
                st.error(f"Input text validation failed: {message}")
                return None, None
            text_content = direct_text.strip()
            source_type = "direct input"
            logger.info("Direct text input processed.")
        else:
            if st.session_state.last_input_hash is not None and st.session_state.last_input_hash != hash((None, "", "")):
                st.warning("Please either upload a file or paste your chat text to proceed.")
            return None, None
        
        if text_content and len(text_content) > Config.MAX_TEXT_LENGTH:
            st.warning(f"The input text is very long ({len(text_content):,} characters). "
                       f"The AI model may struggle with very long inputs, or results might be truncated. "
                       f"Consider using shorter chat exports for better results (max {Config.MAX_TEXT_LENGTH:,} characters).")
        
        return text_content, source_type
        
    except RuntimeError as re:
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
    
    st.subheader("3. ✨ Refine & Convert")
    
    st.markdown("##### Input Statistics")
    stats = TextProcessor.get_text_stats(text_content)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Words", f"{stats['words']:,}")
    with col2:
        st.metric("Characters", f"{stats['characters']:,}")
    with col3:
        st.metric("Paragraphs/Lines", f"{stats['lines']:,}")
    
    # st.markdown("<br>") # Removed extra spacing

    st.markdown("##### Article Title (Optional)")
    article_title = st.text_input(
        "Suggest a title for the generated article:",
        placeholder="Leave blank for AI to generate a title, or enter your own...",
        help="This will be the main title in your exported documents. The AI will try to adhere to it.",
        key="article_title_input",
        value=st.session_state.article_title_input_value, 
        on_change=lambda: st.session_state.__setitem__('article_title_input_value', st.session_state.article_title_input)
    )
    
    st.divider() # Replaced st.markdown("---") for consistent styling

    convert_button_container = st.container()
    with convert_button_container:
        st.markdown("<h4 style='text-align: center; color: #3498DB;'>Ready to Convert?</h4>", unsafe_allow_html=True)
        convert_button = st.button(
            "🚀 Generate Article",
            type="primary",
            use_container_width=True,
            help="Click to start the AI conversion process."
        )
    
    if convert_button:
        success = convert_text_to_article(text_content, main_speaker, article_title)
        if success:
            st.rerun()

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
            llm_handler = get_gemini_handler()
            
            processed_text = TextProcessor.prepare_for_conversion(text_content)
            
            if not processed_text:
                st.error("No meaningful content found after processing. Please check your input.")
                logger.warning("Processed text was empty, conversion halted.")
                return False
            
            start_time = time.time()
            article_content = llm_handler.convert_chat_to_article(
                processed_text, 
                main_speaker, 
                article_title
            )
            processing_time = time.time() - start_time
            
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
    
    st.subheader("4. ✅ Your Generated Article")
    
    st.markdown("##### Output Summary")
    output_stats = TextProcessor.get_text_stats(article_content)
    cols_metrics_output = st.columns(2) # Auto-stacks on mobile
    
    with cols_metrics_output[0]:
        st.metric("Words", f"{output_stats['words']:,}")
        st.metric("Characters", f"{output_stats['characters']:,}")
    with cols_metrics_output[1]:
        st.metric("Paragraphs", f"{output_stats['lines']:,}")
        st.metric("AI Time", f"{processing_time:.1f}s")
    
    # st.markdown("<br>") # Removed extra spacing

    with st.expander("📖 **Click to view and copy your article**", expanded=True):
        st.text_area(
            "Generated Article Content:",
            value=article_content,
            height=500,
            disabled=False,
            key="generated_article_preview_final"
        )
        st.markdown("<small>_To copy, click in the box, then press Ctrl+A (Cmd+A) to select all, followed by Ctrl+C (Cmd+C)._</small>", unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("5. ⬇️ Download Your Article")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            docx_content = DocumentExporter.create_word_doc(
                article_content, 
                article_title or Config.DEFAULT_TITLE
            )
            filename_docx = DocumentExporter.generate_filename(article_title, "docx")
            
            st.download_button(
                label="📝 Download as Word (DOCX)",
                data=docx_content,
                file_name=filename_docx,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="download_docx_button"
            )
        except Exception as e:
            logger.error(f"Error creating DOCX: {e}")
            st.error(f"Failed to create Word document. Please try again or report this issue.")
    
    with col2:
        try:
            pdf_content = DocumentExporter.create_pdf(
                article_content, 
                article_title or Config.DEFAULT_TITLE
            )
            filename_pdf = DocumentExporter.generate_filename(article_title, "pdf")
            
            st.download_button(
                label="📄 Download as PDF",
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
        st.header("📚 About This App")
        st.markdown("""
        The **WhatsApp to Article Converter** leverages advanced AI to transform your chat transcripts 
        into structured, coherent, and professionally formatted articles or book chapters. 
        Ideal for educators, content creators, or anyone wanting to distill knowledge from digital conversations.
        """)
        
        st.subheader("Features:")
        st.markdown("""
        - **Multi-format Input:** Supports TXT, DOCX, and PDF chat exports.
        - **Intelligent Cleaning:** Removes timestamps, emojis, and casual chat.
        - **AI Synthesis:** Uses Google Gemini to synthesize teachings and discussions.
        - **Customizable Output:** Option to specify a main speaker and article title.
        - **Flexible Export:** Download your article as a Word document (.docx) or PDF.
        """)
        
        st.divider()
        
        st.header("💡 Best Practices & Tips")
        st.markdown("""
        - **Specify Main Speaker:** For optimal results, clearly name the teacher/main speaker.
        - **File Size Limit:** Keep uploaded files under 10MB (or ~50,000 characters for direct text).
        - **Content Quality:** The AI performs best with transcripts that contain substantial teaching and well-articulated points.
        - **Privacy Assured:** All content is processed in-memory and is not stored beyond your active session.
        """)
        
        st.divider()
        
        if st.checkbox("Show AI Model Info", help="Developer information about the AI model in use.", key="show_model_info_checkbox"):
            try:
                llm_handler = get_gemini_handler() 
                model_info = llm_handler.get_model_info()
                st.json(model_info)
            except Exception as e:
                st.warning(f"Model info temporarily unavailable: {str(e)}")
                logger.warning(f"Failed to retrieve model info: {e}")

def main() -> None:
    """Main application function orchestrating the Streamlit UI and logic."""
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

    display_sidebar()
    display_header()
    
    # Input section values are now taken from session_state in display_input_section
    uploaded_file_from_session, direct_text_from_session, main_speaker_from_session = display_input_section()

    current_input_hash = hash((
        uploaded_file_from_session.name if uploaded_file_from_session else None,
        direct_text_from_session,
        main_speaker_from_session
    ))

    if current_input_hash != st.session_state.last_input_hash:
        if st.session_state.article_content is not None or st.session_state.last_input_hash is not None:
            st.session_state.article_content = None
            st.session_state.article_title = None
            st.session_state.processing_time = None
            logger.info("New input detected, clearing previous results and rerunning.")
            st.session_state.last_input_hash = current_input_hash
            st.rerun() 
        else:
            st.session_state.last_input_hash = current_input_hash

    # Use values from session state for processing
    text_content, source_type = process_input(uploaded_file_from_session, direct_text_from_session)
    
    if text_content:
        # Input preview expander (now after input & speaker sections, before conversion)
        # Margin-top reduced by custom CSS for expander header
        with st.expander("📖 **Review your cleaned input text**", expanded=False):
            st.info(f"Source: {source_type}")
            cleaned_display_text = TextProcessor.prepare_for_conversion(text_content) 
            preview_text = cleaned_display_text[:1500] + "\n\n... (rest of text truncated for preview) ..." if len(cleaned_display_text) > 1500 else cleaned_display_text
            st.text_area("Cleaned Input Preview", preview_text, height=300, disabled=True, key="input_preview_area_cleaned")
            st.markdown(f"<small>_Showing first {len(preview_text):,} characters of {len(cleaned_display_text):,} characters._</small>", unsafe_allow_html=True)
        
        display_processing_section(text_content, source_type or "", main_speaker_from_session) 
        
    if st.session_state.article_content:
        display_output_section(
            st.session_state.article_content,
            st.session_state.article_title,
            st.session_state.processing_time if st.session_state.processing_time is not None else 0.0
        )

if __name__ == "__main__":
    main()
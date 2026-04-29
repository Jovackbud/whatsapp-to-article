from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import base64
import logging
from src.config import Config
from src.document_handler import DocumentHandler
from src.text_processor import TextProcessor
from src.llm_handler import GeminiHandler
from src.document_export import DocumentExporter

app = FastAPI(docs_url=None, redoc_url=None) # Disable bloat
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# Initialize LLM handler
llm = GeminiHandler()

MISSING_CONTENT_MARKERS = (
    "content you intended to provide",
    "transcript of the whatsapp class",
    "was not included in your message",
    "please paste the transcript below",
    "please paste the transcript",
    "as soon as you provide it",
    "i am ready to act as your ghostwriter",
    "i am ready to transform your material",
    "i am standing by for your text",
    "i understand the instructions perfectly",
    "while adhering strictly to your requirements",
)


def _looks_like_missing_content_response(text: str) -> bool:
    if not text:
        return True
    lowered = text.lower()
    return any(marker in lowered for marker in MISSING_CONTENT_MARKERS)


def _extract_file_text(file: UploadFile) -> str:
    file_extension = file.filename.split('.')[-1].lower()
    file_content = file.file.read()

    if len(file_content) > Config.MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size: {Config.MAX_FILE_SIZE / (1024 * 1024):.1f}MB")

    if file_extension == 'txt':
        return DocumentHandler.extract_text_from_txt(file_content)
    if file_extension == 'docx':
        return DocumentHandler.extract_text_from_docx(file_content)
    if file_extension == 'pdf':
        return DocumentHandler.extract_text_from_pdf(file_content)

    raise ValueError(f"Unsupported file type. Please upload: {', '.join(Config.SUPPORTED_FILE_TYPES)}")


def _resolve_input_text(chat_text: str, file: UploadFile) -> str:
    input_parts = []

    if file and file.filename:
        file_text = _extract_file_text(file).strip()
        if file_text:
            input_parts.append(file_text)

    if chat_text and chat_text.strip():
        is_valid, message = DocumentHandler.validate_text_input(chat_text)
        if not is_valid:
            raise ValueError(message)
        input_parts.append(chat_text.strip())

    combined_text = "\n\n".join(part for part in input_parts if part).strip()
    if not combined_text:
        raise ValueError("Please provide pasted text, an attached file, or both.")

    return combined_text


def _build_result_context(request: Request, article: str, title: str, status_message: str):
    formatted_article = TextProcessor.format_output(article)

    try:
        docx_bytes = DocumentExporter.create_word_doc(formatted_article, title)
        docx_b64 = base64.b64encode(docx_bytes).decode("utf-8")
        docx_uri = f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{docx_b64}"
        docx_file = DocumentExporter.generate_filename(title, "docx")
    except Exception:
        docx_uri, docx_file = None, None

    try:
        pdf_bytes = DocumentExporter.create_pdf(formatted_article, title)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_uri = f"data:application/pdf;base64,{pdf_b64}"
        pdf_file = DocumentExporter.generate_filename(title, "pdf")
    except Exception:
        pdf_uri, pdf_file = None, None

    return templates.TemplateResponse("result.html", {
        "request": request,
        "article": formatted_article,
        "title": title,
        "docx_uri": docx_uri,
        "docx_file": docx_file,
        "pdf_uri": pdf_uri,
        "pdf_file": pdf_file,
        "status_message": status_message,
    })

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/convert", response_class=HTMLResponse)
async def convert(
    request: Request, 
    chat_text: str = Form(""), 
    file: UploadFile = File(None),
    speaker: str = Form(""), 
    title: str = Form("")
):
    try:
        text_content = _resolve_input_text(chat_text, file)
        normalized_text = text_content.strip()

        processed_text = TextProcessor.prepare_for_conversion(text_content)
        if not processed_text:
            raise ValueError("No meaningful content found after processing.")

        article = llm.convert_chat_to_article(processed_text, speaker, title)
        if _looks_like_missing_content_response(article) and processed_text != normalized_text:
            logger.warning("Gemini responded as if no transcript was provided. Retrying with normalized raw text.")
            article = llm.convert_chat_to_article(normalized_text, speaker, title)

        if _looks_like_missing_content_response(article):
            raise RuntimeError("The AI model could not read the pasted transcript correctly. Please try again or upload the content as a TXT file.")

        final_title = title or Config.DEFAULT_TITLE
        return _build_result_context(request, article, final_title, "Article generated successfully.")
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": str(e),
            "chat_text": chat_text,
            "speaker": speaker,
            "title": title,
        })


@app.post("/result/update", response_class=HTMLResponse)
async def update_result(
    request: Request,
    article: str = Form(""),
    title: str = Form(""),
):
    try:
        if not article or not article.strip():
            raise ValueError("Edited article is empty. Please keep some text before saving changes.")

        final_title = title.strip() or Config.DEFAULT_TITLE
        return _build_result_context(request, article.strip(), final_title, "Article updated successfully.")
    except Exception as e:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "article": article,
            "title": title or Config.DEFAULT_TITLE,
            "error": str(e),
            "status_message": None,
            "docx_uri": None,
            "docx_file": None,
            "pdf_uri": None,
            "pdf_file": None,
        })

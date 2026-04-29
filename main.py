from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.config import Config
from src.document_handler import DocumentHandler
from src.text_processor import TextProcessor
from src.llm_handler import GeminiHandler
from src.document_export import DocumentExporter

app = FastAPI(docs_url=None, redoc_url=None) # Disable bloat
templates = Jinja2Templates(directory="templates")

# Initialize LLM handler
llm = GeminiHandler()

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
    text_content = ""
    try:
        if file and file.filename:
            file_content = await file.read()
            file_extension = file.filename.split('.')[-1].lower()
            
            if len(file_content) > Config.MAX_FILE_SIZE:
                raise ValueError(f"File too large. Maximum size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB")
                
            if file_extension == 'txt':
                text_content = DocumentHandler.extract_text_from_txt(file_content)
            elif file_extension == 'docx':
                text_content = DocumentHandler.extract_text_from_docx(file_content)
            elif file_extension == 'pdf':
                text_content = DocumentHandler.extract_text_from_pdf(file_content)
            else:
                raise ValueError(f"Unsupported file type. Please upload: {', '.join(Config.SUPPORTED_FILE_TYPES)}")
        elif chat_text and chat_text.strip():
            is_valid, message = DocumentHandler.validate_text_input(chat_text)
            if not is_valid:
                raise ValueError(message)
            text_content = chat_text.strip()
        else:
            raise ValueError("Please provide either a file or text input.")

        # Process and convert
        processed_text = TextProcessor.prepare_for_conversion(text_content)
        if not processed_text:
            raise ValueError("No meaningful content found after processing.")

        article = llm.convert_chat_to_article(processed_text, speaker, title)
        formatted_article = TextProcessor.format_output(article)
        
        # Generate Export Files Statelessly via Data URIs
        import base64
        final_title = title or Config.DEFAULT_TITLE
        
        try:
            docx_bytes = DocumentExporter.create_word_doc(formatted_article, final_title)
            docx_b64 = base64.b64encode(docx_bytes).decode('utf-8')
            docx_uri = f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{docx_b64}"
            docx_file = DocumentExporter.generate_filename(final_title, "docx")
        except:
            docx_uri, docx_file = None, None

        try:
            pdf_bytes = DocumentExporter.create_pdf(formatted_article, final_title)
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_uri = f"data:application/pdf;base64,{pdf_b64}"
            pdf_file = DocumentExporter.generate_filename(final_title, "pdf")
        except:
            pdf_uri, pdf_file = None, None
        
        return templates.TemplateResponse("result.html", {
            "request": request, 
            "article": formatted_article, 
            "title": final_title,
            "docx_uri": docx_uri,
            "docx_file": docx_file,
            "pdf_uri": pdf_uri,
            "pdf_file": pdf_file
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": str(e)
        })

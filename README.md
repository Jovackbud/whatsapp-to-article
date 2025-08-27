# WhatsApp to Article Converter

A powerful Streamlit application that converts WhatsApp chat exports into well-structured articles or book chapters using Google's Gemini AI.

## 🌟 Features

- **Multiple Input Methods**: Upload TXT, DOCX, or PDF files, or paste text directly
- **AI-Powered Conversion**: Uses Google Gemini to intelligently transform chat conversations
- **Speaker Focus**: Identify main speakers/teachers for better content organization
- **Multiple Export Formats**: Download as PDF, DOCX, or copy to clipboard
- **Smart Processing**: Automatically removes timestamps, system messages, and casual elements
- **Professional Formatting**: Creates readable articles with proper headings and structure

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google API key for Gemini (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatsapp-to-article
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Google API key:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Getting a Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## 📁 Project Structure

```
whatsapp-to-article/
├── app.py                 # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── document_handler.py # File upload and text extraction
│   ├── text_processor.py  # Text cleaning and preprocessing
│   ├── llm_handler.py     # Gemini AI integration
│   └── document_export.py # PDF, DOCX, and clipboard export
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md
```

## 🎯 Usage

1. **Launch the app**: `streamlit run app.py`
2. **Input your content**:
   - Upload a WhatsApp chat export file (TXT, DOCX, or PDF)
   - Or paste text directly into the text area
3. **Specify main speaker** (optional): Enter the name of the primary teacher/speaker
4. **Convert**: Click "Convert to Article" and wait for processing
5. **Export**: Download as PDF/DOCX or copy to clipboard for further editing

## 🛠️ Configuration

### Model Selection (Developer)

Change the AI model by editing your `.env` file:

```bash
# Fast and efficient (recommended)
GEMINI_MODEL=gemini-1.5-flash

# Higher quality output
GEMINI_MODEL=gemini-1.5-pro

# Legacy model
GEMINI_MODEL=gemini-1.0-pro
```

### File Limits

- Maximum file size: 10MB
- Maximum text length: 50,000 characters
- Supported formats: TXT, DOCX, PDF

## 📊 What It Does

The application intelligently:

1. **Cleans chat data**: Removes timestamps, system messages, and casual elements
2. **Identifies speakers**: Recognizes different participants in the conversation
3. **Focuses content**: Emphasizes contributions from specified main speakers
4. **Structures content**: Creates logical sections with headings and proper flow
5. **Formats professionally**: Generates article-style content suitable for publication

## 🔧 Deployment

### Streamlit Community Cloud

1. Push your code to GitHub
2. Connect your repository to [Streamlit Community Cloud](https://share.streamlit.io/)
3. Add your API key in the Streamlit secrets management
4. Deploy!

### Local Production

```bash
# Set production environment
export ENVIRONMENT=production

# Run with optimized settings
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your `GOOGLE_API_KEY` is set correctly in `.env`
2. **File Upload Issues**: Check file size (max 10MB) and format (TXT, DOCX, PDF)
3. **Processing Errors**: Try with shorter text or check your internet connection
4. **Export Problems**: Ensure you have write permissions in the download directory

### Error Reporting

Enable detailed error reporting by checking "Show detailed error" when errors occur.

## 🔒 Privacy & Security

- All processing happens through Google's Gemini API
- No chat content is stored permanently
- Files are processed in memory and not saved to disk
- API keys are handled securely through environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful language processing
- Streamlit for the amazing web framework
- Contributors and users who help improve this tool

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Include error messages and steps to reproduce

---

**Made with ❤️ for better content creation**
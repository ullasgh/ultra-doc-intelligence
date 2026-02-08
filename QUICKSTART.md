# 🚀 Quick Start Guide

Get Ultra Doc-Intelligence running in 5 minutes!

## Prerequisites

- Python 3.9+ installed
- Anthropic API key ([Get one free here](https://console.anthropic.com/))
-Open AI API Key

## Step 1: Setup Backend

```bash
# Clone or navigate to the project
cd ultra-doc-intelligence/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key (choose one method)
# Method 1: Export (Linux/macOS)
export ANTHROPIC_API_KEY='your-key-here'

# Method 2: Set (Windows)
set ANTHROPIC_API_KEY=your-key-here

# Method 3: Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run the server
python app.py
```

✅ Backend running at: http://localhost:8000
📚 API Docs: http://localhost:8000/docs

## Step 2: Setup Frontend

```bash
# Open a new terminal
cd ultra-doc-intelligence/frontend

# Serve with Python's built-in server
python -m http.server 3000

# Or use any other HTTP server:
# npx serve -p 3000
# php -S localhost:3000
```

✅ Frontend running at: http://localhost:3000

## Step 3: Test It Out!

1. Open http://localhost:3000 in your browser
2. Drag & drop a logistics document (PDF, DOCX, or TXT)
3. Ask questions like:
   - "What is the carrier rate?"
   - "When is pickup scheduled?"
   - "Who is the consignee?"
4. Try the "Extract Data" tab for structured extraction

## Docker Alternative

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-key-here'

# Run with Docker Compose
docker-compose up --build
```

Both services will be available at the same URLs.

## Testing the API Directly

```bash
# Upload a document
curl -X POST http://localhost:8000/upload \
  -F "file=@your_document.pdf"

# Response will include doc_id
# {"doc_id": "doc_20260208_143022", ...}

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "doc_20260208_143022",
    "question": "What is the carrier rate?"
  }'

# Extract structured data
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "doc_20260208_143022"
  }'
```

## Troubleshooting

### Port already in use
```bash
# Change the port in app.py (line: uvicorn.run(..., port=8001))
# Or kill the process using port 8000
```

### API key not working
```bash
# Verify it's set correctly
echo $ANTHROPIC_API_KEY  # Linux/macOS
echo %ANTHROPIC_API_KEY%  # Windows

# Make sure there are no extra spaces or quotes
```

### Dependencies not installing
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing one by one
pip install fastapi uvicorn anthropic sentence-transformers
```

### CORS errors in frontend
```bash
# Make sure backend is running first
# Check browser console for detailed error
# Verify API_BASE URL in frontend/index.html (line 134)
```

## Next Steps

- Check out the full [README.md](README.md) for architecture details
- Explore the [API documentation](http://localhost:8000/docs)
- Try different document types
- Test guardrails with out-of-scope questions

---

**Need help?** Open an issue or check the troubleshooting section in README.md
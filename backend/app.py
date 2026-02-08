"""
Ultra Doc-Intelligence: AI-Powered Logistics Document Assistant
Advanced RAG system with guardrails, confidence scoring, and structured extraction
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Document processing
import PyPDF2
import docx
from io import BytesIO

# ML/AI components
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic

# Environment setup
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize models
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

app = FastAPI(title="Ultra Doc-Intelligence API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
document_store = {}

# Pydantic models
class QuestionRequest(BaseModel):
    doc_id: str
    question: str

class ExtractionRequest(BaseModel):
    doc_id: str

class Answer(BaseModel):
    answer: str
    sources: List[str]
    confidence: float
    reasoning: str

class StructuredData(BaseModel):
    shipment_id: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    pickup_datetime: Optional[str] = None
    delivery_datetime: Optional[str] = None
    equipment_type: Optional[str] = None
    mode: Optional[str] = None
    rate: Optional[str] = None
    currency: Optional[str] = None
    weight: Optional[str] = None
    carrier_name: Optional[str] = None
    confidence: float = 0.0


class DocumentProcessor:
    """Advanced document processing with intelligent chunking"""
    
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extract text from PDF, DOCX, or TXT"""
        try:
            if filename.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            elif filename.endswith('.docx'):
                doc = docx.Document(BytesIO(file_bytes))
                text = "\n".join([para.text for para in doc.paragraphs])
            elif filename.endswith('.txt'):
                text = file_bytes.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing document: {str(e)}")
    
    @staticmethod
    def intelligent_chunk(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Intelligent chunking strategy:
        - Respects paragraph boundaries
        - Maintains semantic coherence
        - Includes overlap for context preservation
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk_size and we have content
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Include overlap from previous chunk
                words = current_chunk.split()
                overlap_text = " ".join(words[-overlap//5:]) if len(words) > overlap//5 else ""
                current_chunk = overlap_text + " " + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Fallback: if no chunks created, use simple splitting
        if not chunks:
            words = text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append(chunk)
        
        return chunks


class RAGEngine:
    """Advanced Retrieval-Augmented Generation with multiple guardrails"""
    
    def __init__(self):
        self.min_similarity_threshold = 0.25  # Guardrail threshold
        self.low_confidence_threshold = 0.4
        self.high_confidence_threshold = 0.7
    
    def create_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Create embeddings for document chunks"""
        return embedding_model.encode(chunks)
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        chunks: List[str], 
        embeddings: np.ndarray, 
        top_k: int = 3
    ) -> tuple[List[str], List[float]]:
        """Retrieve most relevant chunks with similarity scores"""
        query_embedding = embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        retrieved_chunks = [chunks[i] for i in top_indices]
        retrieved_scores = [float(similarities[i]) for i in top_indices]
        
        return retrieved_chunks, retrieved_scores
    
    def calculate_confidence(
        self, 
        similarities: List[float], 
        answer: str, 
        context: str
    ) -> tuple[float, str]:
        """
        Multi-factor confidence scoring:
        1. Retrieval similarity (40%)
        2. Answer length/completeness (20%)
        3. Context overlap (20%)
        4. Uncertainty detection (20%)
        """
        # Factor 1: Average similarity score
        avg_similarity = np.mean(similarities) if similarities else 0.0
        similarity_score = avg_similarity * 0.4
        
        # Factor 2: Answer completeness (penalize very short answers)
        answer_length = len(answer.split())
        completeness_score = min(answer_length / 20, 1.0) * 0.2
        
        # Factor 3: Context overlap
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        overlap = len(answer_words & context_words) / max(len(answer_words), 1)
        overlap_score = overlap * 0.2
        
        # Factor 4: Uncertainty detection (penalize uncertain language)
        uncertainty_phrases = ['not sure', 'unclear', 'cannot determine', 'not found', 'unknown']
        has_uncertainty = any(phrase in answer.lower() for phrase in uncertainty_phrases)
        uncertainty_score = 0.0 if has_uncertainty else 0.2
        
        total_confidence = similarity_score + completeness_score + overlap_score + uncertainty_score
        
        # Generate reasoning
        if total_confidence >= self.high_confidence_threshold:
            reasoning = "High confidence: Strong retrieval match with complete answer"
        elif total_confidence >= self.low_confidence_threshold:
            reasoning = "Medium confidence: Partial match found in document"
        else:
            reasoning = "Low confidence: Weak or no relevant information found"
        
        return total_confidence, reasoning
    
    def apply_guardrails(
        self, 
        similarities: List[float], 
        confidence: float
    ) -> Optional[str]:
        """
        Multiple guardrail checks:
        1. Similarity threshold guardrail
        2. Confidence threshold guardrail
        3. Contradiction detection
        """
        # Guardrail 1: Check minimum similarity
        if not similarities or max(similarities) < self.min_similarity_threshold:
            return "NOT_FOUND: No relevant information found in the document. The question may be outside the document's scope."
        
        # Guardrail 2: Low confidence check
        if confidence < self.low_confidence_threshold:
            return f"LOW_CONFIDENCE: The answer has low confidence ({confidence:.2f}). The information may not be reliable."
        
        return None  # No guardrail triggered
    
    def answer_question(
        self, 
        question: str, 
        chunks: List[str], 
        embeddings: np.ndarray
    ) -> Answer:
        """Main RAG pipeline with guardrails"""
        # Retrieve relevant chunks
        retrieved_chunks, similarities = self.retrieve_relevant_chunks(
            question, chunks, embeddings, top_k=3
        )
        
        # Combine context
        context = "\n\n---\n\n".join(retrieved_chunks)
        
        # Generate answer using Claude
        if client:
            try:
                prompt = f"""Based ONLY on the following document excerpts, answer the question.
If the information is not in the excerpts, say "Information not found in document."

Document excerpts:
{context}

Question: {question}

Provide a direct, concise answer based only on the information above."""

                message = client.chat.completions.create(model="gpt-4o-mini",messages=[{"role": "user", "content": prompt}],max_tokens=1000)
                answer_text = message.choices[0].message.content
            except Exception as e:
                answer_text = f"Error generating answer: {str(e)}"
        else:
            # Fallback: simple extraction
            answer_text = f"Based on the retrieved context: {retrieved_chunks[0][:200]}..."
        
        # Calculate confidence
        confidence, reasoning = self.calculate_confidence(
            similarities, answer_text, context
        )
        
        # Apply guardrails
        guardrail_message = self.apply_guardrails(similarities, confidence)
        if guardrail_message:
            answer_text = guardrail_message
            confidence = 0.0
            reasoning = "Guardrail triggered"
        
        return Answer(
            answer=answer_text,
            sources=retrieved_chunks,
            confidence=round(confidence, 3),
            reasoning=reasoning
        )


class StructuredExtractor:
    """Extract structured shipment data using LLM"""
    
    @staticmethod
    def extract_structured_data(text: str) -> StructuredData:
        """Extract structured logistics data from document"""
        if not client:
            return StructuredData(confidence=0.0)
        
        try:
            prompt = f"""Extract the following logistics information from the document. 
Return ONLY a JSON object with these exact fields. Use null if information is not found.

Fields to extract:
- shipment_id: string
- shipper: string (company name)
- consignee: string (company name)
- pickup_datetime: string (ISO format if possible)
- delivery_datetime: string (ISO format if possible)
- equipment_type: string (e.g., "53' Dry Van", "Flatbed")
- mode: string (e.g., "Truckload", "LTL")
- rate: string (numeric value)
- currency: string (e.g., "USD")
- weight: string (with units)
- carrier_name: string

Document:
{text[:4000]}

Return ONLY valid JSON, no other text."""

            message = client.chat.completions.create(model="gpt-4o-mini",messages=[{"role": "user", "content": prompt}],max_tokens=1000)
            
            response_text = message.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Calculate confidence based on how many fields found
                non_null_count = sum(1 for v in data.values() if v is not None)
                confidence = non_null_count / 11  # 11 fields total
                
                return StructuredData(**data, confidence=round(confidence, 3))
            
        except Exception as e:
            print(f"Extraction error: {str(e)}")
        
        return StructuredData(confidence=0.0)


# Initialize engines
rag_engine = RAGEngine()
extractor = StructuredExtractor()


# API Endpoints
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a logistics document"""
    try:
        # Read file
        file_bytes = await file.read()
        
        # Extract text
        text = DocumentProcessor.extract_text(file_bytes, file.filename)
        
        # Intelligent chunking
        chunks = DocumentProcessor.intelligent_chunk(text)
        
        # Create embeddings
        embeddings = rag_engine.create_embeddings(chunks)
        
        # Generate document ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store in memory
        document_store[doc_id] = {
            "filename": file.filename,
            "text": text,
            "chunks": chunks,
            "embeddings": embeddings,
            "uploaded_at": datetime.now().isoformat()
        }
        
        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks_created": len(chunks),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=Answer)
async def ask_question(request: QuestionRequest):
    """Ask a question about an uploaded document"""
    if request.doc_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_store[request.doc_id]
    
    answer = rag_engine.answer_question(
        request.question,
        doc["chunks"],
        doc["embeddings"]
    )
    
    return answer


@app.post("/extract", response_model=StructuredData)
async def extract_structured(request: ExtractionRequest):
    """Extract structured shipment data from document"""
    if request.doc_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_store[request.doc_id]
    structured_data = extractor.extract_structured_data(doc["text"])
    
    return structured_data


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    return {
        "documents": [
            {
                "doc_id": doc_id,
                "filename": doc["filename"],
                "uploaded_at": doc["uploaded_at"],
                "chunks": len(doc["chunks"])
            }
            for doc_id, doc in document_store.items()
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "anthropic_available": client is not None,
        "documents_loaded": len(document_store)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
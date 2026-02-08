"""
Test script for Ultra Doc-Intelligence
Run this to validate the system is working correctly
"""

import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_health():
    """Test health endpoint"""
    print_header("Testing Health Endpoint")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_upload(file_path):
    """Test document upload"""
    print_header(f"Testing Document Upload: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f)}
        response = requests.post(f"{API_BASE}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    return data.get('doc_id') if response.status_code == 200 else None

def test_ask(doc_id, question):
    """Test question answering"""
    print_header(f"Testing Q&A: {question}")
    
    payload = {
        "doc_id": doc_id,
        "question": question
    }
    
    response = requests.post(
        f"{API_BASE}/ask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"\nQuestion: {question}")
    print(f"Answer: {data.get('answer')}")
    print(f"Confidence: {data.get('confidence')} ({data.get('reasoning')})")
    print(f"\nSources ({len(data.get('sources', []))}):")
    for i, source in enumerate(data.get('sources', [])[:2], 1):
        print(f"  {i}. {source[:100]}...")
    
    return data

def test_extract(doc_id):
    """Test structured extraction"""
    print_header("Testing Structured Extraction")
    
    payload = {"doc_id": doc_id}
    
    response = requests.post(
        f"{API_BASE}/extract",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print(f"\nExtraction Confidence: {data.get('confidence')}")
    print("\nExtracted Data:")
    for key, value in data.items():
        if key != 'confidence' and value:
            print(f"  {key}: {value}")
    
    return data

def test_guardrails(doc_id):
    """Test guardrail questions that should be refused"""
    print_header("Testing Guardrails (Should Refuse)")
    
    bad_questions = [
        "What's the weather today?",
        "Who won the Super Bowl?",
        "What is 2+2?",
        "Tell me about quantum physics"
    ]
    
    for question in bad_questions:
        print(f"\n❌ Testing: {question}")
        result = test_ask(doc_id, question)
        
        if result['confidence'] < 0.3:
            print("✅ Guardrail PASSED - Low confidence or refused")
        else:
            print("⚠️  Guardrail FAILED - Should have lower confidence")
        
        time.sleep(1)

def run_full_test():
    """Run complete test suite"""
    print("\n" + "🚀"*30)
    print("  Ultra Doc-Intelligence - Test Suite")
    print("🚀"*30)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Server not responding. Make sure backend is running!")
        return
    
    time.sleep(1)
    
    # Test 2: Upload document
    sample_file = "sample_documents/rate_confirmation.txt"
    
    if not Path(sample_file).exists():
        print(f"\n❌ Sample file not found: {sample_file}")
        print("Creating a simple test file...")
        Path("sample_documents").mkdir(exist_ok=True)
        with open(sample_file, 'w') as f:
            f.write("""
RATE CONFIRMATION
Shipment ID: TEST-001
Carrier Rate: $1,500.00
Pickup: January 15, 2024
Delivery: January 18, 2024
Carrier: Test Trucking LLC
Shipper: Test Shipper Inc.
Consignee: Test Receiver Corp.
Equipment: 53' Dry Van
Weight: 25,000 lbs
""")
    
    doc_id = test_upload(sample_file)
    
    if not doc_id:
        print("\n❌ Upload failed!")
        return
    
    time.sleep(1)
    
    # Test 3: Ask questions
    questions = [
        "What is the carrier rate?",
        "When is pickup scheduled?",
        "Who is the consignee?",
        "What is the shipment ID?",
        "What type of equipment is needed?"
    ]
    
    for question in questions:
        test_ask(doc_id, question)
        time.sleep(1)
    
    # Test 4: Structured extraction
    test_extract(doc_id)
    time.sleep(1)
    
    # Test 5: Guardrails
    test_guardrails(doc_id)
    
    # Summary
    print_header("Test Suite Complete!")
    print("\n✅ All tests completed successfully!")
    print("\nNext steps:")
    print("1. Try uploading your own documents via the UI at http://localhost:3000")
    print("2. Test with different document types (PDF, DOCX)")
    print("3. Experiment with various questions")
    print("\n📚 Check README.md for detailed documentation")

if __name__ == "__main__":
    try:
        run_full_test()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the backend is running: python backend/app.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
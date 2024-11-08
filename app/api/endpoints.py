import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from asyncpg import Connection
from .pdf_handler import extract_text_from_pdf  # function to extract text
from .db import get_db_connection  # Database connection
from groq import Groq

# Load env and initialize Groq client
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define FastAPI app instance
app = FastAPI()

# Define Pydantic model for question requests
class AskQuestionRequest(BaseModel):
    extracted_text: str  # Extracted text
    question: str  # Question
    previous_convo: list[list[str]]  # Previous conversation history

# Endpoint to handle PDF upload, validate size, extract text, and save metadata
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), conn: Connection = Depends(get_db_connection)):
    MAX_FILE_SIZE = 4 * 1024 * 1024  # 4 MB limit
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content and check file size
    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 4 MB limit")
    await file.seek(0)  # Reset file pointer

    # Extract text from PDF and save to database
    text = extract_text_from_pdf(file_data)
    await conn.execute(
        """
        INSERT INTO pdf_metadata (filename, filesize, filecontent, uploaddate)
        VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
        """,
        file.filename, len(file_data), text
    )

    # Return response with filename and extracted text
    return {"filename": file.filename, "extracted_text": text}

# Endpoint to handle question
@app.post("/ask")
async def ask_question(request: AskQuestionRequest):
    try:
        # Generate response from Groq API
        completion = client.chat.completions.create(
            model="llama-3.2-90b-text-preview",
            messages=[
                {"role": "user", "content": f"Context: {request.extracted_text}"},
                {"role": "user", "content": f"Question: {request.question}"},
                {"role": "user", "content": f"Previous Conversation: {request.previous_convo}"}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False  # Get a full response at once
        )

        # Extract and return the answer
        answer = completion.choices[0].message.content if completion.choices else None
        if answer:
            return {"answer": answer}
        else:
            raise HTTPException(status_code=500, detail="No response, try again")

    except Exception as e:
        # return error response
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")

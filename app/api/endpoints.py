import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from asyncpg import Connection
from .pdf_handler import extract_text_from_pdf, upload_pdf_to_s3
from .db import get_db_connection, init_db_pool, close_db_pool
from contextlib import asynccontextmanager
from groq import Groq

# Load environment variables and initialize Groq client
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define FastAPI app instance
app = FastAPI()

# Lifespan event handler to manage setup and teardown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

# Attach lifespan event handler to the app
app.router.lifespan_context = lifespan

# Pydantic model for question requests
class AskQuestionRequest(BaseModel):
    extracted_text: str
    question: str
    previous_convo: list[list[str]]

# Endpoint to handle PDF upload, validate size, extract text, save metadata, upload to S3
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
    await file.seek(0)

    # Extract text from PDF
    text = extract_text_from_pdf(file_data)

    # Upload the PDF file to S3 and get the S3 URL
    s3_url = upload_pdf_to_s3(file_data, file.filename)

    # Save metadata to PostgreSQL database
    await conn.execute(
        """
        INSERT INTO main_pdf_metadata (filename, filesize, filecontent, uploaddate, s3_url)
        VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4)
        """,
        file.filename, len(file_data), text, s3_url
    )

    # Return response with filename, extracted text, and S3 URL
    return {"filename": file.filename, "extracted_text": text, "s3_url": s3_url}

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
            stream=False
        )

        # Extract and return the answer
        answer = completion.choices[0].message.content if completion.choices else None
        if answer:
            return {"answer": answer}
        else:
            raise HTTPException(status_code=500, detail="No response, try again")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")

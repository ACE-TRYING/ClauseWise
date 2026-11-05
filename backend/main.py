
import io

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ai_engine import split_sentences, simplify_batch, make_summary
from risk_engine import find_clauses, score
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Legal Simplify API",
    description="Upload a contract and identify potentially important clauses.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024


def read_text(data: bytes, filename: str) -> str:

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file has no filename."
        )

    extension = filename.lower().rsplit(".", 1)[-1]

    if extension not in ("pdf", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    if extension == "pdf":
        try:
            reader = PdfReader(io.BytesIO(data))

            if reader.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported."
                )

            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")

            return "\n".join(pages)

        except HTTPException:
            raise

        except (PdfReadError, ValueError, OSError):
            raise HTTPException(
                status_code=400,
                detail="The PDF could not be read. Please upload a valid PDF."
            )

    try:
        return data.decode("utf-8-sig")

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The TXT file must use UTF-8 text encoding."
        )


@app.get("/")
def home():
    return {
        "message": "Legal Simplify API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a file."
        )

    extension = file.filename.lower().rsplit(".", 1)[-1]

    if extension not in ("pdf", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    data = await file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The file is too large. Maximum size is 10 MB."
        )

    text = read_text(data, file.filename)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text was found. "
                "This may be a scanned PDF. "
                "Please upload a text-based PDF."
            )
        )

    sentences = split_sentences(text)

    if not sentences:
        raise HTTPException(
            status_code=400,
            detail="No readable sentences were found in this document."
        )

    # Step 1: Detect clauses using the existing rule engine.
    clauses = find_clauses(sentences)

    # Step 2: Explain ALL detected clauses in one Gemini request.
    explanations = simplify_batch(clauses)

    # Step 3: Attach explanations to their original clauses.
    for clause, explanation in zip(clauses, explanations):

        clause["simplified"] = explanation["simplified"]
        clause["changes"] = explanation["changes"]

        clause["why_it_matters"] = explanation["why_it_matters"]
        clause["example"] = explanation["example"]

    # Step 4: Calculate risk using the original rule engine.
    total, level = score(clauses)

    return {
        "sentences": sentences,
        "clauses": clauses,
        "score": total,
        "level": level,
        "summary": make_summary(clauses, level),
        "word_count": len(text.split()),
        "filename": file.filename,
        "disclaimer": (
            "This tool uses rule-based keyword detection and AI-generated "
            "explanations. It does not provide legal advice or determine "
            "whether a contract is safe."
        ),
    }

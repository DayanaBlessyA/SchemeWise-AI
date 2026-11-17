from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services.eligibility import find_eligible_schemes
from services.gemini_service import explain_schemes

app = FastAPI(
    title="SchemeWise AI",
    version="1.0.0",
    description="Government Scheme and Eligibility Assistant"
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class UserProfile(BaseModel):
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1)
    state: str = Field(min_length=1)
    caste: str = Field(min_length=1)
    annual_income: float = Field(ge=0)
    purpose: str = Field(min_length=1)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy", "message": "SchemeWise AI is running"}


@app.post("/schemes/match")
def match_schemes(profile: UserProfile):
    try:
        user_data = profile.model_dump()
        results = find_eligible_schemes(user_data)

        return {
            "total_matches": len(results),
            "results": results
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Scheme matching failed: {str(error)}"
        )


@app.post("/schemes/explain")
def explain_matching_schemes(profile: UserProfile):
    try:
        user_data = profile.model_dump()
        results = find_eligible_schemes(user_data)
        explanation = explain_schemes(user_data, results)

        return {
            "total_matches": len(results),
            "results": results,
            "ai_explanation": explanation,
            "disclaimer": (
                "These are potential matches, not confirmed approvals. "
                "Always verify the latest eligibility rules on the official "
                "government website before applying."
            )
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process your request: {str(error)}"
        )
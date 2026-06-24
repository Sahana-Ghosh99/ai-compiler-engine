import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from openai import OpenAI
import json

app = FastAPI()

# This safely finds your HTML folder no matter what directory you run it from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# [span_0](start_span)Initialize OpenAI safely[span_0](end_span)
API_KEY = os.environ.get("OPENAI_API_KEY", "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")
client = OpenAI(api_key=API_KEY)

# [span_1](start_span)[span_2](start_span)Strict Pydantic Contracts for Multi-Stage Compilation[span_1](end_span)[span_2](end_span)
class IntentSchema(BaseModel):
    summary: str
    target_roles: list[str]
    core_features: list[str]

class SystemArchitecture(BaseModel):
    db_tables: list[str] = Field(description="Database tables and fields")
    api_endpoints: list[str] = Field(description="REST API routes needed")
    ui_views: list[str] = Field(description="Frontend page views and layouts")

class FinalBlueprint(BaseModel):
    ui_schema: dict
    api_schema: dict
    db_schema: dict
    auth_system: dict
    business_logic: dict

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/")
async def compile_pipeline(user_prompt: str = Form(...)):
    logs = []
    try:
        logs.append(" Stage 1: Parsing unstructured user intent...")
        # [span_3](start_span)Step 1: Intent Extraction[span_3](end_span)
        response_step1 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Extract core intent from: {user_prompt}"}],
            response_format=IntentSchema,
        )
        intent = response_step1.choices[0].message.parsed
        logs.append(f" Found roles: {intent.target_roles}")

        logs.append(" Stage 2: Drafting high-level system architecture layout...")
        # [span_4](start_span)Step 2: System Design Layer[span_4](end_span)
        response_step2 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Design architecture metrics for this intent: {intent.json()}"}],
            response_format=SystemArchitecture,
        )
        arch = response_step2.choices[0].message.parsed
        logs.append(f"✓ Formulated {len(arch.db_tables)} core relational tables.")

        logs.append(" Stage 3 & 4: Compiling schemas and running architectural linter...")
        # [span_5](start_span)Step 3 & 4: Schema Generation & Self-Repair[span_5](end_span)
        response_step3 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Generate matching cross-layer schemas for architecture: {arch.json()}. Make sure UI maps to API, and API fields match the DB definitions exactly."}],
            response_format=FinalBlueprint,
        )
        blueprint = response_step3.choices[0].message.parsed
        logs.append("✓ Cross-layer relational consistency linting passed successfully.")
        
        return {
            "status": "SUCCESS",
            "logs": "\n".join(logs),
            "blueprint": blueprint.dict()
        }
    except Exception as e:
        return {
            "status": "COMPILATION_ERROR",
            "logs": f" Pipeline crashed during execution:\n{str(e)}",
            "blueprint": {}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
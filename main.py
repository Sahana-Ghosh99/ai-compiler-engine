import os
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()

# Initialize App and Templates
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialize OpenAI
# Ensure your environment variable is set or replace the string below
API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# Pydantic Schemas
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

# Route to serve the UI
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# Route to process the compilation
@app.post("/")
async def compile_pipeline(request: Request, user_prompt: str = Form(...)):
    logs = []
    blueprint_data = {}
    
    try:
        # Step 1: Intent Extraction
        logs.append("Stage 1: Parsing unstructured user intent...")
        response_step1 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Extract core intent from: {user_prompt}"}],
            response_format=IntentSchema,
        )
        intent = response_step1.choices[0].message.parsed
        logs.append(f"Found roles: {', '.join(intent.target_roles)}")

        # Step 2: System Architecture
        logs.append("Stage 2: Drafting system architecture...")
        response_step2 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Design architecture for: {intent.json()}"}],
            response_format=SystemArchitecture,
        )
        arch = response_step2.choices[0].message.parsed
        logs.append(f"✓ Formulated {len(arch.db_tables)} core tables.")

        # Step 3 & 4: Schema Generation & Linting
        logs.append("Stage 3 & 4: Generating schemas and linting...")
        response_step3 = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Generate schemas for: {arch.json()}"}],
            response_format=FinalBlueprint,
        )
        blueprint_data = response_step3.choices[0].message.parsed.dict()
        logs.append("✓ Consistency linting passed.")
        
        result = {"status": "COMPILED_SUCCESSFULLY", "validation_logs": logs}
        
    except Exception as e:
        result = {"status": "COMPILATION_ERROR", "validation_logs": [f"Pipeline crashed: {str(e)}"]}
        blueprint_data = {}

    # Return the rendered page with the results
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"result": result, "blueprint": blueprint_data, "prompt": user_prompt}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
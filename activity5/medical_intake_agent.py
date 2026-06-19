import os
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Symptom(BaseModel):
    symptom_name: str
    severity: Severity
    duration_days: int = Field(ge=0)

class MedicalIntake(BaseModel):
    symptoms: list[Symptom]
    allergies: list[str]
    urgency_rating: int = Field(ge=1, le=10)
    clinical_reasoning: str

def process_intake(patient_input: str) -> MedicalIntake:
    max_retries = 3
    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": f"""You are a medical intake AI assistant. Extract and structure the patient's medical information from their input.
                    
Respond ONLY with a JSON object in this exact format (no markdown, no extra text):
{{
    "symptoms": [
        {{"symptom_name": "string", "severity": "LOW|MEDIUM|HIGH", "duration_days": number}},
        ...
    ],
    "allergies": ["string", ...],
    "urgency_rating": number (1-10),
    "clinical_reasoning": "explanation of triage and severity selections"
}}

Patient input: {patient_input}"""
                }
            ]
        }
    ]
    
    for attempt in range(1, max_retries + 1):
        try:
            # Call Gemini API
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to parse as MedicalIntake
            intake_data = eval(response_text)  # Using eval for JSON parsing (Gemini returns valid JSON)
            record = MedicalIntake(**intake_data)
            print(f"Validation passed on attempt {attempt}")
            return record
            
        except ValidationError as e:
            print(f"\nValidation Error on attempt {attempt}:")
            print(e)
            
            if attempt < max_retries:
                # Append error feedback to contents for next retry
                error_feedback = f"""The previous response failed validation with the following errors:
{str(e)}

Please correct the response and ensure:
1. urgency_rating is between 1 and 10 (inclusive)
2. duration_days is >= 0
3. severity is one of: LOW, MEDIUM, HIGH
4. All required fields are present

Provide only the corrected JSON object, nothing else."""
                
                contents.append({"role": "assistant", "parts": [{"text": response_text}]})
                contents.append({"role": "user", "parts": [{"text": error_feedback}]})
            else:
                raise Exception(f"Failed to get valid medical intake record after {max_retries} attempts")
        
        except Exception as e:
            print(f"\n✗ Error on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise Exception(f"Failed to process intake after {max_retries} attempts: {str(e)}")

if __name__ == "__main__":
    # Test input
    test_input = "My stomach is cramping incredibly badly since last night! The pain is unbearable, definitely an urgency of 15 out of 10! I don't think I have allergies."
    try:
        record = process_intake(test_input)
        print("\n--- Validated Intake Record ---")
        print(record.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed: {e}")
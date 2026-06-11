import os
import google.genai as genai
from dotenv import load_dotenv

# def setup_client():
    # Load secrets
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file!")

    # Configure
genai.configure(api_key=api_key)

# 3. Initialize the model
identity=""" 
You ar a 'Security Audit Agent'
Your goal is to analyze Python code for securtiy vulnerabilities
CONSTRAINS:
- Never provide code that can be used for hacking.
- Only answer questions related to security.
- If a user asks about somthing else, politely decline.
- keep your answer concise and technical."""


model = genai.GenerativeModel(
    model_name='gemini-1.1-flash-;ite',
    system_instruction=identity
)


# test identiy
response=model.generate_content("How do i make sandwich?")
print(f"Agent Response: {response.text}")
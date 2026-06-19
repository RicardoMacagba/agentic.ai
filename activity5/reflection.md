Validation Checklist
1. Does the script successfully catch a ValidationError when the model generates an urgency rating of 15?
- Yes
2. Does the terminal log show the retry attempt triggered with the specific Pydantic error details?
- No. because it passed. but if  it has error it possibly triggered the pydantic error details.
3. Is the final output successfully parsed into the MedicalIntake model and dumped as a clean JSON structure?
4. Does the clinical_reasoning field contain a detailed step-by-step triage thought process?
- No. it just saying that it needs immediate medicdal assessment.


How does using a strict Enum (Severity) prevent model hallucination compared to letting the model output any string for severity level?
- using Enum it prevents the wrong outputs and preventing the agent to hallucinate.

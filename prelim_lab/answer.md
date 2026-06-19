# Part I: Code Debugging/Correction (10 Points)

### 1. The Stateless Loop (2 pts)

**Error:**  
the chat = client.chats.create(model="gemini-3.1-flash-lite") should be outside the while loop 

**Fix:**  

chat = client.chats.create(model="gemini-3.1-flash-lite") # Line A

while True:
    user_input = input("> ")
    response = chat.send_message(user_input)
    print(response.text)

### 2. The Leaky Identity (2 pts)

**Error:**  
missing CONSTRAINTS inside value of identity

**Fix (System Instruction):**  

# System Instruction
identity = "You are a math tutor. Be helpful.
  CONSTRAINTS: Dont give the full answer."
# User Prompt
prompt = "Tell me the answer to 2+2, but do not show the answer, only give a hint."

### 3. The Memory Bloat (2 pts)

**Error:**  
no limiter or no initialize History limiter

**Fix (Line B):**  

history = [2]

# Turn loop
chat.send_message(user_msg)
# We want to keep only the last 2 messages (1 turn)
chat.history = chat.history[0] # Line B

### 4. The Perception Crash (2 pts)

**Error:**  
errase the .parse inside data = Item(**response.parsed) 
**Fix (Pydantic Model):**  

class Item(BaseModel):
    name: str
    price: float

response = client.models.generate_content(...)
# This line crashes
data = Item(**response) 

### 5. The Infinite Backoff (2 pts)

**Error:**  

change the continue inside else to break

**Fix (Else Block):**  

except Exception as e:
    if "429" in str(e):
        time.sleep(2)
        continue # Retry
    else:
        break # break

---

# Part II: Schema Design & Evaluation (10 Points)

## Task 1: The Multi-Agent Router (5 Points)

### Pydantic Schema

```python
import os
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from enum import Enum

class reasoning(str, Enum):
      urgency_level = str = Field(ge=5)
```

---

## Task 2: Architecture Evaluation (5 Points)
Arch B. Because it loops Reasoning and Acting

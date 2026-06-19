import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

HOTEL_DATABASE = {
    "tokyo": [
        {"name": "Shibuya Grand", "price_per_night": 180},
        {"name": "Imperial Palace Stay", "price_per_night": 450},
        {"name": "Capsule Capsule", "price_per_night": 45}
    ],
    "paris": [
        {"name": "Hotel de L'Opera", "price_per_night": 220},
        {"name": "Ritz Paris", "price_per_night": 950},
        {"name": "Montmartre Hostel", "price_per_night": 70}
    ]
}

def is_safe(text: str) -> bool:
    """Check if text contains malicious keywords"""
    malicious_keywords = ["delete", "drop", "hack", "exploit", "injection", "sql", "script", "admin", "free room", "override price", "ignore rules", "bypass validation"]
    text_lower = text.lower()
    for keyword in malicious_keywords:
        if keyword in text_lower:
            return False
    return True

def search_hotels(city: str) -> str:
    """Search hotels in a given city from the database"""
    city_lower = city.lower().strip()
    if city_lower not in HOTEL_DATABASE:
        return f"No hotels found in {city}. Available cities: {', '.join(HOTEL_DATABASE.keys())}"
    
    hotels = HOTEL_DATABASE[city_lower]
    result = f"Hotels in {city}:\n"
    for hotel in hotels:
        result += f"- {hotel['name']}: ${hotel['price_per_night']}/night\n"
    return result

def book_hotel(hotel_name: str, budget: float = 200.0) -> str:
    """Book a hotel if it's within the budget"""
    hotel_name_lower = hotel_name.lower().strip()
    
    # Search through all cities for the hotel
    for city, hotels in HOTEL_DATABASE.items():
        for hotel in hotels:
            if hotel['name'].lower() == hotel_name_lower:
                if hotel['price_per_night'] <= budget:
                    return f"Booking confirmed: {hotel['name']} in {city} (${hotel['price_per_night']}/night)"
                else:
                    return f" {hotel['name']} costs ${hotel['price_per_night']}/night, which exceeds your budget of ${budget}/night"
    
    return f"Hotel '{hotel_name}' not found in database"

def agent_loop():
    """Main agent loop with tool use and history management"""
    print("Welcome to Sky Luxe Hotel Agent!")
    print("Commands: search <city>, book <hotel_name> <budget>, exit")
    print("-" * 50)
    
    history = []
    max_history_len = 3
    
    system_prompt = """You are a helpful hotel booking assistant. You have access to tools:
1. search_hotels(city) - Find available hotels in a city
2. book_hotel(hotel_name, budget) - Book a hotel if within budget

When the user asks about hotels, parse their request and suggest using the tools."""
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            # Safety check
            if not is_safe(user_input):
                print("Agent: Your request contains suspicious content. Please try again.")
                continue
            
            # Parse user input for tool calls
            tool_result = None
            if user_input.lower().startswith("search "):
                city = user_input[7:].strip()
                tool_result = search_hotels(city)
                print(f"Agent: {tool_result}")
            
            elif user_input.lower().startswith("book "):
                parts = user_input[5:].strip().split()
                if len(parts) >= 2:
                    hotel_name = " ".join(parts[:-1])
                    try:
                        budget = float(parts[-1])
                        tool_result = book_hotel(hotel_name, budget)
                        print(f"Agent: {tool_result}")
                    except ValueError:
                        print("Agent: Please provide budget as a number. Usage: book <hotel_name> <budget>")
                else:
                    print("Agent: Please provide hotel name and budget. Usage: book <hotel_name> <budget>")
            
            else:
                # Use Gemini for general conversation
                history.append({
                    "role": "user",
                    "parts": [{"text": user_input}]
                })
                
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=[{"role": "user", "parts": [{"text": system_prompt}]}] + history
                )
                
                assistant_message = response.text
                print(f"Agent: {assistant_message}")
                
                history.append({
                    "role": "assistant",
                    "parts": [{"text": assistant_message}]
                })
                
                # Prune history if it gets too long
                if len(history) > max_history_len:
                    history = history[-max_history_len:]
        
        except KeyboardInterrupt:
            print("\nAgent: Goodbye!")
            break
        except Exception as e:
            print(f"Agent: An error occurred: {e}")

if __name__ == "__main__":
    agent_loop()
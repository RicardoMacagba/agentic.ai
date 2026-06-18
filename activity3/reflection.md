Step 5: Verification
Save all files to activity3 including the screenshots of output.

Did the agent output TOOL: get_weather('Manila')?
- Yes!

Did the final answer incorporate the 32°C data?
- yes! It has.

Reflection: Why did we have to send [user_query, response.text, observation] as a list in Turn 2?
- because the model needs the full context. the original question, what it decided to do previously and the result from that action, 
so it can decide whether to call another tool or provide the final answer.
import google.generativeai as genai
from config import API_KEY

print("Testing API key...")
print(f"API Key: {API_KEY[:10]}...")

genai.configure(api_key=API_KEY)

# Test with gemini-2.5-flash
print("\nTesting gemini-2.5-flash model...")
model = genai.GenerativeModel('gemini-2.5-flash')

print("Sending test request...")
response = model.generate_content("Say hello in one sentence")

print("Response received:")
print(response.text)
print("\n✅ API key works!")
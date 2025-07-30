import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variable
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    print("Error: DEEPSEEK_API_KEY not found in .env file or environment variables.")
    exit()

# Configure the DeepSeek API client
try:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    print(f"Error configuring DeepSeek API: {e}")
    exit()

# Test the API with a simple prompt
prompt = "Hello, DeepSeek! Tell me a fun fact."
print(f"Sending prompt: {prompt}")

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024,
        temperature=0.7
    )
    
    print("\nResponse from DeepSeek:")
    print(response.choices[0].message.content)
    print("\nAPI Key test successful!")
except Exception as e:
    print(f"Error during API call: {e}")
    print("API Key test failed.")

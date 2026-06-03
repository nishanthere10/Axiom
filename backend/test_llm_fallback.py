import os
# We will temporarily mock the API keys to test fallback
os.environ["GROQ_API_KEY"] = "invalid_groq_key"
os.environ["GEMINI_API_KEY"] = "dummy_gemini"

from services.llm_provider import generate_chat_completion, get_instructor_client
import litellm

def test_fallback():
    print("Testing Fallback to Gemini (since Groq key is invalid)...")
    try:
        response = generate_chat_completion(
            messages=[{"role": "user", "content": "Say hello!"}],
            model="groq/llama-3.3-70b-versatile" # This will fail due to invalid key
        )
        print("Response received successfully!")
        print("Model used:", response.model)
    except Exception as e:
        print("Test failed, exception:", e)

if __name__ == "__main__":
    test_fallback()

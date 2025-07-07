from groq import AsyncGroq
import sys
import os

# Make the config library available for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.config import settings

class GroqClient:
    """
    A client for interacting with the Groq API.
    It encapsulates the logic for creating chat completions.
    """
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in the environment.")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def create_chat_completion(self, prompt: str, model: str = "llama3-70b-8192") -> str:
        """
        Generates a chat completion using the specified prompt and model.

        Args:
            prompt: The instruction and data to send to the model.
            model: The LLM to use for the completion.

        Returns:
            The content of the chat completion as a JSON string.
            
        Raises:
            Exception: If the API call fails or returns an empty response.
        """
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            response_content = chat_completion.choices[0].message.content
            if not response_content:
                raise ValueError("Groq API returned an empty response.")
            return response_content
        except Exception as e:
            # In a production system, you'd have more specific error handling
            # and logging here.
            print(f"Error communicating with Groq API: {e}")
            raise 
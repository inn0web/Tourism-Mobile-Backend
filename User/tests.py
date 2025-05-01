from django.test import TestCase
from decouple import config
from openai import OpenAI

message = "I'm looking for cozy coffee shops with free Wi-Fi near a park or a bookstore"

client = OpenAI(
            api_key=config("OPENAI_API_KEY") 
        )

def extract_google_places_searchable_keywords_from_user_message(message):

        instruction = f"""
        You are an assistant designed to extract relevant and concise 
        searchable keywords from a user's message. These keywords will be 
        used to query the Google Places API for location-based results.

        Focus on nouns and key descriptors relevant to location searches, 
        such as types of places, amenities, and specific geographic locations 
        (e.g., city names). Avoid filler words like "near", "with", "looking for", 
        "want", etc.

        Return only the most useful and specific keywords that best represent 
        the user's intent. Format your response as a simple, comma-separated list, 
        with no additional text or explanation.

        Example format: coffee shop, Wi-Fi, bookstore, Amsterdam

        Message:
        {message}
        """


        response = client.responses.create(
            model="gpt-4o-mini",
            input=instruction
        )

        return response.output_text.strip('"').split(',')

print(extract_google_places_searchable_keywords_from_user_message(message))
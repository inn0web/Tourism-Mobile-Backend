import json
from googlemaps import Client
from django.conf import settings
import requests

class Feed:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = Client(key=self.api_key)

    def get_places_from_google_maps(self, city_name, city_location: tuple, user_interests: list) -> dict:
        
        # Dictionary to store results
        user_feed = {
            "recommended": [],
            "popular": [],
        }

        for interest in user_interests:

            places = self.client.places_nearby(
                location=city_location,
                radius=5000,  # Search within 5km radius
                keyword=interest
            )

            for place in places["results"]:

                # Check if the place has photos
                if "photos" not in place:
                    continue

                place_image_reference = place["photos"][0]["photo_reference"]
                # Construct the image URL using the photo reference
                image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={place_image_reference}&key={self.api_key}"

                place_rating = place.get("rating", "Not Rated")

                # Prepare common data
                place_data = {
                    "name": place["name"],
                    "place_id": place["place_id"],
                    "tag": interest,
                    "city_name": city_name,
                    "image": image_url,
                    "rating": place_rating,
                }

                try:
                    if place_rating != "Not Rated" and float(place_rating) >= 4.5:
                        user_feed["popular"].append(place_data)
                    else:
                        user_feed["recommended"].append(place_data)
                except (ValueError, TypeError):
                    # Fallback if rating can't be converted to float
                    user_feed["recommended"].append(place_data)

        return user_feed

    def get_place_details(self, place_id, city_name=None) -> dict:
        """
        Fetches detailed information about a place using its place_id.
        """
        request_place_details = requests.get(
            f"https://places.googleapis.com/v1/places/{place_id}?fields=*&key={self.api_key}"
        )

        request_data = request_place_details.json()

        # extract required fields from response
        place_data = {
            "place_id": request_data["id"],
            "name": request_data["displayName"]["text"],
            "address": request_data["formattedAddress"],
            "phone": request_data.get("internationalPhoneNumber"),
            "rating": request_data["rating"],
            "reviews": [
                {
                    "author": review["authorAttribution"]["displayName"],
                    "text": review["text"],
                    "rating": review["rating"],
                    "author_image": review["authorAttribution"]["photoUri"],
                    "publish_time": review["publishTime"]
                } for review in request_data["reviews"]
            ],
            "photos": [
                {
                    "url": photo["authorAttributions"][0]["photoUri"]
                } for photo in request_data["photos"]
            ],
            "opening_hours": request_data.get("currentOpeningHours"),
            "map_directions": request_data["googleMapsLinks"]["directionsUri"],
            "write_a_review_url": request_data["googleMapsLinks"]["writeAReviewUri"]
        }

        if city_name is not None:
            place_data["city_name"] = city_name
        
        return place_data
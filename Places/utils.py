import json
from googlemaps import Client
from django.conf import settings

class Feed:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = Client(key=self.api_key)

        #photo:
        # https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference=YOUR_PHOTO_REFERENCE&key=YOUR_API_KEY

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

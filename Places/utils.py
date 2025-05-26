import json
from googlemaps import Client
from django.conf import settings
import requests
import random

class Feed:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = Client(key=self.api_key)

        self.google_places_base_url = 'https://places.googleapis.com/v1'

    def get_places_from_google_maps_for_ai_request(self, city_name, city_location, extracted_search_interests_from_message):

        place_ids = []
        place_details = []

        # search for places based on extracted interests
        for interest in extracted_search_interests_from_message:

            places = self.client.places_nearby(
                location=city_location,
                radius=5000,  # Search within 5km radius
                keyword=interest
            )

            for place in places["results"]:

                if len(place_ids) >= 5:
                    break

                # make sure this place has images
                if "photos" not in place:
                    continue

                place_ids.append(place["place_id"])

        # get the detail of each place and append to list
        for place_id in place_ids:

            place_detail = self.get_place_details(
                place_id=place_id, 
                is_ai_request=True,
                city_name=city_name
            )

            place_details.append(place_detail)

        return place_details

    def get_places_from_google_maps(self, city_name, city_location, user_interests):
        
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

                try:
                    place_image_reference = place["photos"][0]["photo_reference"]
                    # Construct the image URL using the photo reference
                    image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={place_image_reference}&key={self.api_key}"

                except KeyError:    
                    continue
                
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

        # shuffle the lists to randomize the order
        
        random.shuffle(user_feed["recommended"])
        random.shuffle(user_feed["popular"])

        return user_feed

    def get_place_details(self, place_id, is_ai_request=False, city_name=None) -> dict:
        """
        Fetches detailed information about a place using its place_id.
        """
        request_place_details = requests.get(
            f"{self.google_places_base_url}/places/{place_id}?fields=*&key={self.api_key}"
        )

        request_data = request_place_details.json()

        # print(json.dumps(request_data, indent=4))

        # extract required fields from response
        place_data = {
            "place_id": request_data["id"],
            "name": request_data["displayName"]["text"],
            "address": request_data["formattedAddress"],
            "phone": request_data.get("internationalPhoneNumber"),
            "rating": request_data.get("rating", ""),
            "photos": [
                {
                    "url": f"{self.google_places_base_url}/{photo['name']}/media?key={self.api_key}&maxHeightPx=400&maxWidthPx=400",
                } for photo in request_data["photos"]
            ],
            "opening_hours": request_data.get("currentOpeningHours"),
            "map_directions": request_data["googleMapsLinks"]["directionsUri"],
        }

        # https://places.googleapis.com/v1/NAME/media?key=API_KEY&PARAMETERS

        if city_name is not None:
            place_data["city_name"] = city_name

        if not is_ai_request and request_data.get("reviews"):
            place_data["reviews"] = [
                {
                    "author": review["authorAttribution"]["displayName"],
                    "text": review.get("text", ""),
                    "rating": review["rating"],
                    "author_image": review["authorAttribution"]["photoUri"],
                    "publish_time": review["publishTime"]
                } for review in request_data["reviews"] if review.get("text") and review.get("rating")
            ]
            
            place_data["write_a_review_url"] = request_data["googleMapsLinks"]["writeAReviewUri"]
        
        return place_data
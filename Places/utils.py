import json
from googlemaps import Client
from django.conf import settings
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

class Feed:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = Client(key=self.api_key)
        self.google_places_base_url = 'https://places.googleapis.com/v1'

    def get_places_from_google_maps_for_ai_request(self, city_name: str, city_location: tuple, extracted_search_interests_from_message: list) -> list:
        place_ids = set()
        place_details = []

        # search for places based on extracted interests
        for interest in extracted_search_interests_from_message:
            places = self.client.places_nearby(
                location=city_location,
                radius=5000,
                keyword=interest
            )
            for place in places["results"]:
                if len(place_ids) >= settings.MAX_NUMBER_OF_PLACES_TO_FETCH_FOR_AI_REQUEST:
                    break
                if "photos" not in place:
                    continue
                place_ids.add(place["place_id"])
            if len(place_ids) >= settings.MAX_NUMBER_OF_PLACES_TO_FETCH_FOR_AI_REQUEST:
                break

        # Fetch details in parallel for efficiency
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    self.get_place_details,
                    place_id=pid,
                    is_ai_request=True,
                    city_name=city_name
                )
                for pid in place_ids
            ]
            for future in as_completed(futures):
                detail = future.result()
                if detail:
                    place_details.append(detail)

        return place_details

    def get_places_from_google_maps(self, city_name: str, city_location: tuple, user_interests: list, is_search_request=False):
        user_feed = {
            "recommended": [],
            "popular": [],
        }
        seen_place_ids = set()

        for interest in user_interests:
            places = self.client.places_nearby(
                location=city_location,
                radius=5000,
                keyword=interest
            )
            for place in places["results"]:
                if "photos" not in place or place["place_id"] in seen_place_ids:
                    continue
                seen_place_ids.add(place["place_id"])
                try:
                    place_image_reference = place["photos"][0]["photo_reference"]
                    image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={place_image_reference}&key={self.api_key}"
                except KeyError:
                    continue

                place_rating = place.get("rating", "Not Rated")
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
                    user_feed["recommended"].append(place_data)

        if not is_search_request:
            random.shuffle(user_feed["recommended"])
            random.shuffle(user_feed["popular"])

        return user_feed

    def get_place_details(self, place_id: str, tag=None, is_ai_request=False, is_saved_place_request=False, city_name=None) -> dict:
        try:
            request_place_details = requests.get(
                f"{self.google_places_base_url}/places/{place_id}?fields=*&key={self.api_key}"
            )
            request_data = request_place_details.json()
        except Exception:
            return {}

        place_data = {
            "place_id": request_data.get("id", ""),
            "name": request_data.get("displayName", {}).get("text", ""),
            "address": request_data.get("formattedAddress", ""),
            "rating": request_data.get("rating", ""),
        }
        if tag is not None:
            place_data["tag"] = tag
        if city_name is not None:
            place_data["city_name"] = city_name

        if not is_saved_place_request:
            place_data["photos"] = [
                {
                    "url": f"{self.google_places_base_url}/{photo['name']}/media?key={self.api_key}&maxHeightPx=400&maxWidthPx=400",
                } for photo in request_data.get("photos", [])
            ]
            place_data["opening_hours"] = request_data.get("currentOpeningHours")
            place_data["map_directions"] = request_data.get("googleMapsLinks", {}).get("directionsUri")
            place_data["phone"] = request_data.get("internationalPhoneNumber")
        else:
            photos = request_data.get("photos", [])
            if photos:
                place_data["image"] = f"{self.google_places_base_url}/{photos[0]['name']}/media?key={self.api_key}&maxHeightPx=400&maxWidthPx=400"

        if not is_ai_request and request_data.get("reviews") and not is_saved_place_request:
            place_data["reviews"] = [
                {
                    "author": review.get("authorAttribution", {}).get("displayName", ""),
                    "text": review.get("text", ""),
                    "rating": review.get("rating", ""),
                    "author_image": review.get("authorAttribution", {}).get("photoUri", ""),
                    "publish_time": review.get("publishTime", "")
                } for review in request_data["reviews"] if review.get("text") and review.get("rating")
            ]
            place_data["write_a_review_url"] = request_data.get("googleMapsLinks", {}).get("writeAReviewUri")
        return place_data
import json
from django.test import TestCase
from googlemaps import Client
import requests

place_id = "ChIJrQ0oiRq_UBMR40rgtsd0TiU"


def get_place_from_requests():
    
    response = requests.get(
        f"https://places.googleapis.com/v1/places/{place_id}?fields=*&key=AIzaSyCyKMdG6AdJFfC6YY_Oe9C4O8ic_TH8Geo"
    )

    with open("reques_detail_place.json", "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=4, ensure_ascii=False)

gmaps = Client(key="AIzaSyCyKMdG6AdJFfC6YY_Oe9C4O8ic_TH8Geo")

def places():

    # Define the location (latitude, longitude of Pogradec)
    location = (40.9025, 20.6525)

    # Define search queries
    search_terms = ["Drink & Dance", "Accommodation", "Nature"]

    # Dictionary to store results
    search_results = {}

    for term in search_terms:
        places = gmaps.places_nearby(
            location=location,
            radius=5000,  # Search within 5km radius
            keyword=term
        )
        
        search_results[term] = places.get("results", [])

    # Save to JSON file
    with open("search_result.json", "w", encoding="utf-8") as f:
        json.dump(search_results, f, indent=4, ensure_ascii=False)

def place():

    _place = gmaps.place(place_id=place_id)

    with open("place.json", "w", encoding="utf-8") as f:
        json.dump(_place, f, indent=4, ensure_ascii=False)

place()
# get_place_from_requests()

# https://places.googleapis.com/v1/places/ChIJrQ0oiRq_UBMR40rgtsd0TiU/photos/AeeoHcLjPZNsjTF8vumu50a0f8VKaByWfl9UMGs2Wjr2pT72Y5u0wbVeu-k7y3i7Ux_vBKIaqcTM_1guMa63KBQuD7siV95EW_e2HezBrgNp5jfzSRVCyUTo0B9PlQP2TiryXDpHruFByCTTlwRrymTL6wUIvRHdFMQtf_aA8xa-sS2y8enYGwk3zcbeVfGInGoJHNuuGp0zizBcX-JePy4j6GiR8vWF1H1-79F_F6gDkywizvHK5tdd1mS9UToFnBAAZoAax9qwyppIqUA8Fms9tbyOLuqa8r8n2eVskEi8wDv_ymHZaS4i1cAT_7_aW_cdjg4ZLCpDcuGar0R5aDp5mTdH4LE3MgkDCxOl97V2ohyxXTUEjQsJKEWimu5Fzdgu1z0ZjOICWfWaXjKO4YbFSvtOdWkdz4jqOvUJB379Qxk/media?maxHeightPx=400&maxWidthPx=400&key=AIzaSyCyKMdG6AdJFfC6YY_Oe9C4O8ic_TH8Geo
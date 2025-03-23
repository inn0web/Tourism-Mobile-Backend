from django.test import TestCase
from googlemaps import Client

gmaps = Client(key="AIzaSyBkLSTOWXu6Kypc5RJf-g9n_BmadeqB4RU")

# Define the location (latitude, longitude of Pogradec)
location = (40.9025, 20.6525)

# Define search queries
search_terms = ["Drink & Dance", "Accommodation", "Nature"]


for term in search_terms:
    places = gmaps.places_nearby(
        location=location,
        radius=5000,  # Search within 5km radius
        keyword=term
    )

    print(f"Results for '{term}':")
    for place in places.get("results", []):
        print(place)
    print("\n" + "="*50 + "\n")


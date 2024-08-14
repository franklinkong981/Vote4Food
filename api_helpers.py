"""This file contains the functions that will be used by the app to call the PositionStack Geolocating API to convert a zip code into 
coordinates or the Spoonacular API to search for restaurants or menu items. The functions will return the JSON data in the response object."""

import os
import requests

GEOLOCATION_API_URL = "http://api.positionstack.com/v1/forward"
SPOONACULAR_RESTAURANT_SEARCH_URL = "https://api.spoonacular.com/food/restaurants/search"
SPOONACULAR_MENU_ITEM_SEARCH_URL = "https://api.spoonacular.com/food/menuItems/search"

def get_address_info(zip_code):
    """Calls the Position Stack Geolocation API which converts the zip_code into an address object that contains information like
    longitude, latitude, region, etc. Returns the long/lat coordinates in the most relevant/first address object found and raises 
    an error if no results are found."""
    response = requests.get(GEOLOCATION_API_URL, params={"access_key": os.environ.get('POSITION_STACK_API_KEY'), "query": str(zip_code)})
    if len(response.json()['data']) == 0:
        raise ValueError("The zip code you entered is not a registered US zip code.")
    address_data = response.json()['data'][0]
    return {'longitude': float(address_data['longitude']), 'latitude': float(address_data['latitude'])}

def get_restaurant_search_results(search_query, latitude, longitude):
    """Calls the Spoonacular API Restaurant Search route and returns the list of restaurant JSON objects that match the search
    query and are located near the latitude and longitude."""

    restaurants_response = requests.get(SPOONACULAR_RESTAURANT_SEARCH_URL, params={"apiKey": os.environ.get('SPOONACULAR_API_KEY'), "query": search_query, "lat": latitude, "lng": longitude, "distance": 5})
    restaurants_data = restaurants_response.json()["restaurants"]
    return restaurants_data

def get_menu_items_json(restaurant_chain, offset):
    """Calls the Spoonacular API Menu Item Search route and returns the list of menu item JSON objects (max. 100) that match the search query
    which is the name of a restaurant chain. An offset is also provided in case there are more than 100 menu items that match the query.
    Also contains some metadata including the total number of menu items there are in the results."""

    menu_items_response = requests.get(SPOONACULAR_MENU_ITEM_SEARCH_URL, params={"apiKey": os.environ.get('SPOONACULAR_API_KEY'), "query": restaurant_chain, "number": 100, "offset": offset})
    return menu_items_response.json()

def get_menu_items_only(restaurant_chain, offset):
    """Calls the Spoonacular API Menu Item Search route and returns the list of menu item JSON objects (max. 100) that match the search query
    which is the name of a restaurant chain. An offset is also provided in case there are more than 100 menu items that match the query.
    Only the list of menu items matching the search query are returned, no metadata."""

    menu_items_response = requests.get(SPOONACULAR_MENU_ITEM_SEARCH_URL, params={"apiKey": os.environ.get('SPOONACULAR_API_KEY'), "query": restaurant_chain, "number": 100, "offset": offset})
    return menu_items_response.json()['menuItems']


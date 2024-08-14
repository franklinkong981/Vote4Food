"""This file contains helper functions for managing menu item data that don't have to do with calling an API or managing a database."""

def does_item_belong_to_restaurant(item_obj, restaurant_chain):
    """Determines whether the menu item stored in item_obj belongs to a certain restaurant chain. item_obj should be one of the menu
    item JSON data returned by the Spoonacular API."""

    return item_obj['restaurantChain'] == restaurant_chain
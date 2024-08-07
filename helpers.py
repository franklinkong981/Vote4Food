"""This file contains helper functions that don't have to do with calling an API or managing a database."""

##############################################################################
# Functions for managing restaurant data.

def build_restaurant_address_string(address_obj):
    """Each restaurant JSON object returned by the Spoonacular API should have an address object. This function converts this address
    object into an address string that can be easily stored in the restaurant database. Returns None if there is no address."""

    address_components = []
    if 'street_addr' in address_obj:
        address_components.append(address_obj['street_addr'])
    if 'city' in address_obj:
        address_components.append(address_obj['city'])
    if 'state' in address_obj:
        address_components.append(address_obj['state'])
    if 'zipcode' in address_obj:
        address_components.append(address_obj['zipcode'])
    
    if len(address_components) == 0:
        return None
    else:
        return ', '.join(address_components)

def build_restaurant_cuisine_string(cuisines):
    """Each restaurant JSON object should have a cusines array that lists out the different cuisines the restaurant is associated with.
    This function turns this array into a string or None if the arra is empty."""

    if len(cuisines) == 0:
        return None
    else:
        return ', '.join(cuisines)

def get_restaurant_photo_url(restaurant):
    """Grabs the URL for the photo that will be displayd for a particular restaurant, by first looking in its store photos, then
    its logo photos. If no photos are found, returns None."""

    if len(restaurant['store_photos']):
        return restaurant['store_photos'][0]
    elif len(restaurant['logo_photos']):
        return restaurant['logo_photos'][0]
    else:
        return None
    
def format_phone_number(phone_number):
    """Each restaurant JSON object should have a numeric phone number that's either 10 or 11 digits. This function formats it into a string."""

    phone_number_string = str(phone_number)
    if len(phone_number_string) == 10:
        return "(" + phone_number_string[0:3] + ")-" + phone_number_string[3:6] + "-" + phone_number_string[6:]
    elif len(phone_number_string) == 11:
        return phone_number_string[0:1] + "-(" + phone_number_string[1:4] + ")-" + phone_number_string[4:7] + "-" + phone_number_string[7:]
    else:
        return None
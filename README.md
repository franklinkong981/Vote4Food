# [Vouch4Food](https://vouch4food.onrender.com) - A Guide

## Overview

Vouch4Food is a website where you can review restaurant locations that you've been to, as well as menu items you've eaten at these
restaurants. This way, other users will be able to see which menu items at restaurants are the most popular and the most enjoyed.
Since sometimes different customers may have different experiences at the same restaurant due to the menu items they order, having
restaurant and menu item reviews would help other users have a better understanding of what makes a restaurant popular or unpopular.

## Walkthrough

Vouch4Food consists of 2 main features: The ability to bookmark their favorite restaurants/menu items (so that users can access them easily
from the navigational bar on the top of every page) and the ability for users to create, edit, and delete their own reviews for restaurants/menu items.

Upon first visiting the website, users will be directed to the homepage.

![Logged Out Home Page](/static/images/logged_out_home.png)

From here, they can click on "Get Started" to create an account. They will be prompted to enter a first name (required), last name(required), email address (required, must be a valid email, and can't be an email associated with an account that's already been created), the URL to their profile picture (optional, if kept blank the default Vouch4Food Burger photo will be their profile picture), and a password that must be at least 8 characters long.

If the account creation is successful, they will then be redirected to the Log In page, where they will sign in using their email address and password. 

Once login is successful, they will be taken to the logged in homepage.

![Logged In Home Page](/static/images/logged_in_home.png)

On the homepage, you'll see there are buttons to access your favorite restaurants/menu items as well as reviews you've written for restaurants/menu items. 

Below that, you'll see the button to set your current location, which takes you to a form where you can set the zip code you live in (must be a valid 5-digit US postal code). Once you've set your location, the approximate coordinates for the zip code you've set will be calculated and a list of nearby restaurants will then be displayed on your home page.

![Restaurants Near You Home Page Listings](/static/images/restaurants_near_you.png)

On the top of each page once you've logged in, you'll see a navigation bar. On the very top of the navbar, you'll see links that will take you straight to your homepage, dropdowns to access lists of your favorite restaurants/menu items and your reviews for restaurants/menu items, and the option to log out.

You'll also see your profile picture as a thumbnail with your full name next to it. Clicking on that will take you to your profile information page.

![Profile Information Page](/static/images/profile_info.png)

On this page, you'll see all your profile information, and have the option of updating your profile information such as your name, email, etc. You also have the option of resetting your password and setting/updating your current zip code location.

Below the navbar is the restaurant search bar, which is also present on every page. You can search for restaurants by typing in a search query and a valid 5-digit US postal zip code, and you'll be taken to a page that lists out the restaurants near this zip code that match your search query.

![Restaurant Search Results Page](/static/images/restaurant_search.png)

If you click on any of these restaurant search results, a new tab will open and you'll be taken to the profile page for that restaurant location.

![Subway Profile Page](/static/images/restaurant_details.png)

The above picture you see is a profile page for a Subway location in California. You'll see detailed information about the restaurant on this page, such as its address, coordinates, phone number, details about the restaurant, the cuisines it specializes in, and its opening hours.

Below the name of the restaurant, you'll see buttons where you can add the restaurant to your list of favorite restaurants (you'll also have the option of removing it from your list of favorite restaurants afterwards by clicking on the same button) and creating a review for the restaurant. 

When creating a review for the restaurant, you need to input a title and content for your review. Upon submission, your review will be displayed on the restaurant's profile page.

At the bottom of the restaurant location's profile page, you'll also see all reviews for the restaurant location by all users, sorted newest first. Each review has the title, content, and date/time the review was first created. You'll also have the options to edit or delete the reviews you wrote. You can't do the same for reviews written by other users.

![Subway Location Reviews](/static/images/restaurant_review.png)

Also on the restaurant details page is a button that will take you to the list of menu items the restaurant chain offers, which is sorted in chronological order.

![Subway Chain Menu Items Page ](/static/images/menu_item_search.png)

If you click on any of the menu items, you'll see the menu item profile page. This is just like the restaurant profile page. You'll see a picture of the menu item, the name of the item, and which restaurant it's form. You'll also see the buttons to add/remove the menu item to/from your list of favorite menu items, create your own review for the menu item, and edit/delete the reviews for this menu item that you've already written. Finally, you'll see all the reviews for the menu item among all users listed in chronological order (newest first) at the bottom of the page.

![Subway Meataball Marinara Profile Page](/static/images/menu_item_details_review.png)

## APIs Used and Link to Website

Spoonacular (for restaurant and menu item lookup): https://spoonacular.com/food-api

Positionstack (for geocoding, zip code to longitude/latitude coordinates conversion): https://positionstack.com/ 

[Visit Vouch4Food here](https://vouch4food.onrender.com)

## Installation Instructions

You need to have Python 3, pip3, and PostgreSQL installed in order to run this app locally. Because the URL/password for the online Supabase database this website is connected to will not be provided, you will need to create your own (initially empty) database.

Copy the SSH URL for this repo, then in your terminal/command line, navigate to the folder you want and do:

```
git clone ssh_url_here
```

There should be a folder called Vote4Food created, navigate into it.

```
cd Vote4Food
```

Next, set up a virtual environment.

```
python3 -m vev venv
source venv/bin/activate
```

Finally, install all dependencies listed in the requirements.txt file to install all dependencies/software to run this app.

```
pip3 install -r requirements.txt
```

Finally, in order to run the app, you need to create an .env file in the root directory of the repo. You'll need to create an account on the websites for the [PositionStack API](https://positionstack.com/) and [Spoonacular API](https://spoonacular.com/food-api), both of which have free tiers, to generate a unique API key for each of them. 

In addition, in a separate window on your terminal, you'll need to create 2 psql databases: One database that your app will run on and a separate database for testing. They need to be called vouch4food and vouch4food_test, respectively.

```
createdb vouch4food;
createdb vouch4food_test;
```

Check to make sure the databases have been created by doing:

```
psql
\l
```

This will list out the databases you created in psql. You should see vouch4food and vouch4food_test among them.

Finally, in your .env file, include these 4 lines:

```
DATABASE_URL=postgresql:///vouch4food
SECRET_KEY=Vouch4FoodSecretKey
POSITION_STACK_API_KEY=YOUR_POSITIONSTACK_API_KEY
SPOONACULAR_API_KEY=YOUR_SPOONACULAR_API_KEY
```

Now you should be all set to run your app. To do so, uncomment the lines from 940-943 in app.py and in the terminal, do:

```
python3 -m app.py
```

Now, in the browser of your choice, go to localhost:5000/ and you should be at the Vouch4Food home page, you are now running the app locally!

## Tools Used

Copyright 2024. Created with the following tech stack:

Frontend: HTML, CSS, JavaScript, Bootstrap

Backend: Python, Flask, Jinja, WTForms, Python unittest

Database: SQL, PostgreSQL, SQLAlchemy, Supabase.

Deployed on Render.com
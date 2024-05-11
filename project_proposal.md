PROPOSAL: <br>Have you ever been to a restaurant and wished you could see pictures of the menu items? Or wondered what the most popular dishes there were? Or the general opinion of a specific dish that looks interesting? I plan to offer a solution with a website where users can search up specific restaurants they’ve been to and leave reviews for it, as well as more specific reviews for individual dishes they had at the restaurant. Each restaurant will have a menu section that consists of the individual menu items at the restaurant, and users can post pictures of the menu items under each section. Users can also mark their favorite restaurants, as well as upvote/downvote restaurants and menu items. The menu items section can be sorted to display the most liked items at the restaurant based on upvotes/downvotes. Finally, when leaving a review for a restaurant, users can mark what dishes they had which will show up at the top of the review.

Tech stack: What tech stack will you use for your final project?<br>
I plan to use HTML, CSS/Bootstrap, JavaScript, Axios, Python, Flask, PostgreSQL, SQLAlchemy, WTForms, and Bcrypt for user registration/login.

Type: Will this be a website? A mobile app? Something else?<br> This will be a website.

Goal: What goal will your project be designed to achieve?<br> This website will aim to give more context to restaurant reviews by having users mark what dishes they had. It will also have a menu section where users can see pictures, information, and reviews of specific menu items at a restaurant and see the most well-liked dishes.

Users: What kind of users will visit your app? In other words, what is the demographic of your users?<br> The demographic will be towards the general public. Anyone who wants to know specific information about a restaurant in terms of what the menu items look like and what the most popular dishes can go to this website.

Data: What data do you plan on using? How are you planning on collecting your data?<br> I would like to use an API that returns a list of restaurant(s) information, by passing in parameters like address, city, state, zip code, etc. This is how users will be able to search up restaurants. The API should also return information about menu items at a specific restaurant if you pass in a restaurant-specific parameter like a restaurant id. So far I am still looking for an API, but a likely candidate is the OpenMenu API. I plan to store user account information, as well as a user’s favorite restaurants, reviews, and upvotes/downvotes in a PostgreSQL database, and plan on having routes for users to upvote/downvote a restaurant/menu item, as well as create, read, update, and delete their own reviews.



Current Projected Tasks:<br>
Determine database schema.<br>
Test out restaurant/restaurant menu API routes.<br>
Determine user flow (different pages of the website).<br>
Determine user signup information needed and account settings.<br>
User authentication (registration, login, logout)<br>
Determine process of (routes, frontend/backend, etc.) of adding reviews.<br>
Determine process of upvoting/downvoting restaurants and menu items.<br>
Determine layout of restaurant page and menu item page.<br>
Determine process of users favoriting restaurants and menu items.<br>
User authorization (can only edit and delete their own reviews, favorites, and upvotes/downvotes).<br>
User authorization (user can’t access registration and login page once they’re logged in).<br>
Implement search bar.<br>
Determine and implement layout of home page.<br>
Stretch Goals:<br>
Users can add to wish list of future restaurants they want to visit.<br>
Reset password email link.<br>
Tips section where users can post the best hacks at a restaurant.<br>


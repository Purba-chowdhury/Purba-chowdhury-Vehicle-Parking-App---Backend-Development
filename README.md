Project Title - Vehicle Parking App - V1:
It is a multi-user app (one requires an administrator and other users) that manages different parking lots, parking spots and parked vehicles.

1. Technologies Used: 

Backend:
Flask – Lightweight and flexible Python web framework
Flask-SQLAlchemy – ORM for managing and querying SQLite database
sqlite3 – Simple file-based database for development
Matplotlib – Used for generating graphical insights and analytics

Frontend:
Jinja2 – Templating engine for rendering dynamic HTML
Bootstrap  – For user friendly design
HTML, CSS – html for making webpage and CSS provides the style to the webpages.

2. Admin functionalities:

a. Admin can create, edit, update and delete parking lot.
b. Admin can see the registered user and their activities.
c. Admin can view the details of a booked spot. 
d. Admin can view the summary of revenue made by various parking_spot.
e. Admin can edit his/her own profile.

3. User functionalities:

a. User can register to the app and login to the dashboard.
b. User can book a spot of a particular parking_lot. 
c. User can view the summary of user's parking history.
d. User can edit his/her own profile.


4. Install dependencies:

 pip install Flask SQLAlchemy pytz matplotlib

 
5. Running the Application

TO Start the Flask application:

python app.py


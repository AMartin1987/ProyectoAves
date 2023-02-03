# Fallen Birds and Shelters for Birds
#### Video Demo:  https://youtu.be/TxXu8eZZEtg

[This is my final project submitted as a requirement for completing CS50: Introduction to Computer Sciences]

#### Description:
Found a lost or injured bird? Want to provide a shelter for lost birds? This web app allows users to display information about lost birds who need a new home or a place to recover, as well as locations offered as shelters for birds. It displays this information in an interactive Google Map. Registered users can also add new entries of lost birds and locations proposed as shelters for birds. The user's control panel allows them to update their own records or delete them. It has a responsive design that displays the site adequately in desktop as well as mobile devices.

It was designed with Flask, SQLite3, Bootstrap 5, Javascript, a tiny bit of JQuery and integration with the Google Maps and Google Places APIs.

The app makes use of several Python libraries such as:
* [__Flask_login__](https://flask-login.readthedocs.io/en/latest/), for user session management (logging in, logging out, and 'remember me' functionality).
* [__Werkzeug utilities__](https://werkzeug.palletsprojects.com/en/2.2.x/utils/), for handling password hashes.
* [__WTForms__](https://wtforms.readthedocs.io/en/3.0.x/), for form validation and CSRF protection.
* [__Flask-Uploads__](https://pythonhosted.org/Flask-Uploads/), for file uploading and serving the uploaded files (i.e., images of birds).
* [__urllib.parse__](https://docs.python.org/3/library/urllib.parse.html), for breaking URL strings up in components (addressing scheme, network location, path etc.) and combining them back into a URL string.

It also implements a method of url sanitization as explained in [https://www.pythonkitchen.com/how-prevent-open-redirect-vulnerab-flask/]

#### Some issues that should be fixed in the future:
* Rewrite some parts to reduce redundancy (e.g.,if-then expressions).
* Implement email verification for new members. 
* Implement a password recovery feature.
* Implement regular users/administrator account privileges.
* Fix issue: Google Map won't load sometimes after logging in (probable problem regarding order of loading elements in DOM).
* Fix security issue regarding passing values from the database to the Javascript code in search.html. 
* Optimize database and app.py to handle redundant entries (e.g., markers are displayed wrongly in the Google Map when more than one bird or shelter are located in the same address).
* Fix database configuration so it doesn't need to use "check_same_thread=False" to avoid an error message. As explained in the [SQLite3 documentation](https://docs.python.org/3/library/sqlite3.html):
*"__check_same_thread (bool)__ – If True (default), only the creating thread may use the connection. If False, the connection may be shared across multiple threads; if so, write operations should be serialized by the user to avoid data corruption."*
* Fix some issues in the style and responsive design.

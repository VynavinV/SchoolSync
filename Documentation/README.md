
Workspace:# Project README

## Overview

This project is a web application for managing clubs and events at Harold M Brathwaite S.S. It includes features for user authentication, club and event management, and an admin panel for administrative tasks.

## Pages (Each Page will have its own mobile variant)

### Home Page
- **URL:** `/`
- **Description:** Redirects to the login page if the user is not logged in. If logged in, it fetches the user's role and displays the clubs.


### All Clubs Page
- **URL:** `/allClubs`
- **Description:** Displays all the clubs.

### Delete Club
- **URL:** `/delete_club`
- **Description:** Deletes a club. Only accessible by users with the appropriate role.

### Tech Page
- **URL:** `/tech` or `/tech/<category>`
- **Description:** Displays clubs filtered by category. Redirects to the login page if the user is not logged in.

### Club Page
- **URL:** `/club/<int:club_id>`
- **Description:** Displays the details of a specific club. Redirects to the login page if the user is not logged in.

### Announcements Page
- **URL:** `/announcements.html/<int:club_id>`
- **Description:** Displays and manages announcements for a specific club. Redirects to the login page if the user is not logged in.

### Business Page
- **URL:** `/Buisness.html`
- **Description:** Displays the Business page. Redirects to the login page if the user is not logged in.

### Events Page
- **URL:** `/Events.html` or `/Events.html/<category>`
- **Description:** Displays events filtered by category. Redirects to the login page if the user is not logged in.

### Login Page
- **URL:** `/login`
- **Description:** Displays the login page.

### Admin Panel
- **URL:** `/AdminPanel`
- **Description:** Displays the admin panel for managing clubs and events. Only accessible by admin users.

### Verify Login
- **URL:** `/verifyLogin`
- **Description:** Verifies login credentials and redirects to the Google OAuth2 authorization URL.

### Callback
- **URL:** `/callback`
- **Description:** Handles the OAuth2 callback and sets up the user session.

### Check Registration
- **URL:** `/check_registration/<int:club_id>`
- **Description:** Checks if the user is registered for a specific club.

### Register Club
- **URL:** `/register_club`
- **Description:** Registers the user for a club.

### Logout
- **URL:** `/logout`
- **Description:** Logs out the user and clears the session.

### Add Club
- **URL:** `/addClub`
- **Description:** Displays the form to add a new club. Only accessible by admin users.

### Add Events
- **URL:** [`/addEvents.html`]
- **Description:** Displays the form to add a new event. Only accessible by admin users.

### Manage Club
- **URL:** `/manageClub/<int:club_id>`
- **Description:** Manages a specific club. Only accessible by club admins or site-wide admins.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- SQLite
- PIL (Pillow)
- APScheduler
- Google OAuth2 Client Library

### Installation

1. **Download the folder**

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   - Delete database.db for new use case

4. **Set up the OAuth2 client secrets:**
   - Place your [`client_secret.json'] file in the root directory of the project.

5. **Run the application:**
   ```sh
   python main.py
   ```

6. **Access the application:**
   - Open your web browser and go to [`http://127.0.0.1:5001`(this will be replaced by the domain you are hosting on)].

### Configuration

- **Secret Key:** Update the [`app.secret_key`] with a real secret key.
- **OAuth2 Client ID:** Update the [`CLIENT_ID`] with your Google OAuth2 Client ID.
- **Upload Folder:** Ensure the [`UPLOAD_FOLDER`] directory exists or will be created.

### Scheduler

- The application uses APScheduler to delete expired events every hour. This is initialized in [`main.py`]

### Notes

- Ensure that the [`client_secret.json`]file is correctly configured for Google OAuth2.
- The application uses SQLite for the database. The database schema is defined in [`schema.sql`]
- The api should be open so additions to UI should not cause issues.
- Ensure to always back up data before changes (database.db and the Uploads folder)

## Authors

- Vynavin Vinod
- Akshat Goenka
- Madheswaran Kamal

## License

This project is owned and maintained by Vynavin Vinod, Madheswaran Kamal, and Akshat Goenka. As well as Harold M. Brathwaite S.S.
Removal of Credits or copyright disclaimer is prohibited.

## issues
- For any issues, Contact the authors via the 'Contact us' button on the home page or with vinod.vynavin@gmail.com, saturnv24@gmail.com, or 1036928@pdsb.net
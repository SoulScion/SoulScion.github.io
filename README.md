# Games Catalog - Web Application

A application that interacts with the MySQL databse, "games_catalog".
The database contains around 500 video game entires, however not every entry has every single colum of every table filled.


## Architecture

- Frontend:
    - HTML, CSS, Javascript
- Backend:
    - Python (Flask) API
- Database:
    - mySQL (`games_catalog`)

## Requirements

- Python 3.10+
- MySQL 8.0+
- Python Packages: `pip install -r flask flask-cors mysql-connector-python python-dotenv`

## Configuration

Create a `.env` file in the project root:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=[Your Username (usualy "root")]
MYSQL_PASSWORD=[Your Password]
MYSQL_DATABASE=games_catalog

```

NOTE: If you have used mySQL before in order to run this database, you should alreaddy know the password. It's the same one you use to connect to the server in mySQL.


## Full Setup Process

## Option 1 - Using the MySQL Dump File:

### Step 1:

- After creating the .env file, clone the Repo:
    - `git clone https://github.com/SoulScion/SoulScion.github.io.git`

### Step 2:

- Open the MySQL Client/Workbench and start a new connection.

- Run this line in a new file or in the Workbench Terminal:
    - `SOURCE games_catalog_dump.sql;`
- If that doesn't work, you need to give it the full path to the file, something like:
    - `SOURCE C:/Users/example/.../example/SoulScion.github.io/games_catalog_dump.sql;`

- This will give you the entire database with all tables already filled with the data I grabbed.

### Step 3:

- Navigate to the backend directory and then make sure you've installed the required python packages from above.
- After adding the packages, run:
    - `python app.py` OR `python3 app.py`

- Keep this backend Flask server running.

### Step 4:

- In a new terminal, navigate to the frontend directory.
- Then, start a simple Python HTTP server:
    - `python -m http.server 8000`

### Step 5:

- Go to a browser and enter `http://localhost:8000` or whichever port number you used.
- The "Games Catalog" application should pop up and become interactable.

## Option 2 - Running the Import Scripts:

### Step 1:
    - This method is not recommended.
    - However, if you are having issues with Option 1, this is the alternative.

    - Start by creating the .env file and then cloning the Repo:
    - `git clone https://github.com/SoulScion/SoulScion.github.io.git`

### Step 2:

- Open the MySQL Client/Workbench and start a new connection.

- Run this line in a new file or in the Workbench Terminal:
    - `SOURCE schema.sql;`
- If that doesn't work, you need to give it the full path to the file, something like:
    - `SOURCE C:/Users/example/.../example/SoulScion.github.io/schema.sql;`

### Step 3:

- Navigate to the "info_imports" directory and then make sure you've installed the required python packages from above.
- Then, you must run the python scripts in "info_imports" in this order in a terminal:

```
python collect_rawg.py
python import_to_db.py
python import_prices.py
python import_socials.py
python import_perspectives.py
python import_dlcs.py
```

- After running the scripst, navigate to the backend directory and run:
    - `python app.py` OR `python3 app.py`
- Keep this backend Flask server running.

- *From here, just follow Steps 4 and 5 from Option 1.*


## All Interactions in Application:

1. Searching and Browsing Data:
    - The main tab, labeld "Game Directory", of the applicaiton displays a table of all 500 video game entries in the catalog.
        - The search bar allows a user to find any game they desire within the catalog.

2. Displaying Related Data:
    - Double-clicking on any entry in the "Games Directory" tab provides a popup that gives a more detailed view of all relevant information about that entry within the database.
    - Additionally, the "Report" tab details two differnt summaries, the second one is based aroudn standlone games or rather, entries in the catalog that have no dlc. Entries that have no additional content for a game can greatly influence a potential buyer into purchasing different games, making this interesting infromation.

3. Adding and Removing Data:
    - The "Modify" tab allows a user to add a new developer or publisher to the database, while also allowing for the removal of any and all developers and publishers. 
        - For a real product, this would be locked to the company or person behind the webite with a login system, but that functionality goes well beyond the scope of this project.

4. Updating Data:
    - The "Modify" tab has a third subtab that allows a user to edit the numbers of copies a specific game has sold. Since this number can change drastically throughout a game's lifespan, it is crucial to have a quick way to change it.

5. Summarizing Data:
    - The second summary the "Report" tab details consists of the top genres based on the average price of games within that genre. This summary provides a good reflection of how genre may affect price based on the catalog's information.

6. Additional Operation - Bookmark Tab:
    - A "Bookmarks" tab was created in order to collect any number of games into a new table for faster viewing by a user.
    - While the bookmarks aren't persistent across reloads of the website, due to the fact that a soltuion would invovle a login system which goes beyond the scope of this project, they still give a way for a user to seperate data into what they want to view/analyze versus not.
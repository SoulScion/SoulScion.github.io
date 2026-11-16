# Games Catalog - Web Application

A application that interacts with the mySQL databse, "games_catalog". 
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

Create `.env` in the project root:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=[Your Username (usualy "root")]
MYSQL_PASSWORD=[Your Password]
MYSQL_DATABASE=games_catalog

```

NOTE: If you have used mySQL before in order to run this database, you should alreaddy know the password. It's the same one you use to connect to the server in mySQL.
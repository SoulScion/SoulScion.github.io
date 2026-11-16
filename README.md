# Games Catalog - Web Application

A Github Pages (WIP) browser frontend, backed by a Flask and a MySQL API.


## Architecture

Browser (HTML/JS) → Flask API → MySQL (`games_catalog`)

## Requirements

- Python 3.10+
- MySQL 8.0+
- Python Packages: `pip install -r flask flask-cors mysql-connector-python python-dotenv`

## Configuration

Create `.env` in the project root:

```
RAWG_API_KEY=[Your Project API KEY]

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=[Your Username (usualy "root")]
MYSQL_PASSWORD=[Your Password]
MYSQL_DATABASE=games_catalog

```
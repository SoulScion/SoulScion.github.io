-- Schema File - Games Catalog:

-- Refreshing the Database:
DROP DATABASE IF EXISTS games_catalog;

CREATE DATABASE games_catalog;
USE games_catalog;
SELECT DATABASE();

-- Creation of Database Tables:
CREATE TABLE publishers (
    publisher_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    rawg_publisher_id BIGINT UNIQUE,
    publisher_name VARCHAR(150) NOT NULL,
    publisher_city VARCHAR(150),
    publisher_country VARCHAR(150)
);

CREATE TABLE games (
    game_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    rawg_id BIGINT UNIQUE,
    publisher_id INT,
    title VARCHAR(150) NOT NULL,
    copies_sold INT CHECK (copies_sold >= 0),
    earliest_release DATE,
    game_engine VARCHAR(150),
    FOREIGN KEY (publisher_id)
    REFERENCES Publishers(publisher_id)
);

CREATE TABLE developers (
    developer_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    rawg_developers_id BIGINT UNIQUE,
    company_name VARCHAR(150) NOT NULL,
    lead_developer VARCHAR(150),
    employee_count INT CHECK (employee_count > 0),
    developer_city VARCHAR(150),
    developer_country VARCHAR(150)
);

CREATE TABLE platforms (
    platform_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    rawg_platforms_id BIGINT UNIQUE,
    platform_name VARCHAR(150) NOT NULL,
    type VARCHAR(150) CHECK (type IN ('Console', 'PC', 'Mobile', 'Handheld', 'Handheld/Console Hybrid')),
    manufacturer VARCHAR (150),
    release_date DATE
);

CREATE TABLE prices (
    price_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    game_id INT,
    platform_id INT, 
    regular_price DECIMAL(10, 2) CHECK (regular_price > 0),
    price_type VARCHAR(50) DEFAULT 'Standard',
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (platform_id)
    REFERENCES platforms(platform_id)
);

CREATE TABLE dlcs (
    dlc_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    game_id INT,
    name VARCHAR(150) NOT NULL,
    regular_price DECIMAL(10, 2) CHECK (regular_price > 0),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id)
);

-- Essentially, if dlc_id is NULL, then we are talking about the game's deal price.
    -- If the dlc_id is not NULL though, then we are talking about the dlc's deal price.

CREATE TABLE deal_prices (
    deal_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    game_id INT NOT NULL,
    dlc_id INT,
    lowest_price DECIMAL(10, 2) CHECK (lowest_price > 0),
    website_link VARCHAR(150),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id), 
    FOREIGN KEY (dlc_id)
    REFERENCES dlcs(dlc_id)
);

-- Developer/Platform Joint Tables:
   
CREATE TABLE game_credits (
    game_id INT NOT NULL,
    developer_id INT NOT NULL,
    PRIMARY KEY(game_id, developer_id),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (developer_id)
    REFERENCES developers(developer_id)
);

CREATE TABLE game_availability (
    game_id INT NOT NULL,
    platform_id INT NOT NULL,
    PRIMARY KEY(game_id, platform_id),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (platform_id)
    REFERENCES platforms(platform_id)
);

-- Game Filters:

CREATE TABLE genres (
    genre_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    rawg_genre_id BIGINT UNIQUE,
    genre_name VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE game_genres (
    game_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY(game_id, genre_id),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (genre_id)
    REFERENCES genres(genre_id)
);

CREATE TABLE social_types (
    type_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    type_name VARCHAR(150) UNIQUE NOT NULL
        CHECK (type_name IN (
            'Singleplayer', 'Multiplayer', 'Massively Multiplayer', 
            'Local CO-OP', "Online CO-OP", 'PvP', 'PvE', 'Other'))
);

CREATE TABLE game_socials (
    game_id INT NOT NULL,
    type_id INT NOT NULL,
    PRIMARY KEY(game_id, type_id),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (type_id)
    REFERENCES social_types(type_id)
);

CREATE TABLE perspectives (
    perspective_id INT PRIMARY KEY UNIQUE NOT NULL AUTO_INCREMENT,
    perspective_name VARCHAR(150) UNIQUE NOT NULL
        CHECK (perspective_name IN (
            'First-Person', 'Third-Person', 'Isometric', 
            '2D', 'Text-based', 'Top Down', 'Virtual Reality', 
            '2D-HD', 'Cockpit View', 'Fixed Camera', 'Other'))
);

CREATE TABLE game_perspectives (
    game_id INT NOT NULL,
    perspective_id INT NOT NULL,
    PRIMARY KEY(game_id, perspective_id),
    FOREIGN KEY (game_id)
    REFERENCES games(game_id),
    FOREIGN KEY (perspective_id)
    REFERENCES perspectives(perspective_id)
);

SHOW TABLES;

-- Views and Indexes:
CREATE VIEW three_game_pillars AS
SELECT
    games.game_id,
    games.title,
    games.earliest_release,
    games.game_engine,
    developers.company_name,
    publishers.publisher_name,
    platforms.platform_name
FROM games 
INNER JOIN game_credits
ON games.game_id = game_credits.game_id
INNER JOIN developers
ON game_credits.developer_id = developers.developer_id
INNER JOIN publishers
ON games.publisher_id = publishers.publisher_id
INNER JOIN game_availability
ON games.game_id = game_availability.game_id
INNER JOIN platforms
ON game_availability.platform_id = platforms.platform_id
WHERE platforms.type = 'Console';

CREATE INDEX index_reg_price
ON prices(regular_price);







USE games_catalog;
SELECT COUNT(*) AS total_games FROM games;
SELECT COUNT(*) AS total_publishers FROM publishers;
SELECT COUNT(*) AS total_developers FROM developers;
SELECT COUNT(*) AS total_platforms FROM platforms;

SELECT COUNT(*) AS total_prices FROM prices;
SELECT COUNT(*) AS total_dlcs FROM dlcs;
SELECT COUNT(*) AS total_deals FROM deal_prices;

SELECT COUNT(*) AS total_credits FROM game_credits;
SELECT COUNT(*) AS total_avail FROM game_availability;

SELECT COUNT(*) AS total_genres FROM genres;
SELECT COUNT(*) AS total_ggenres FROM game_genres;

SELECT COUNT(*) AS total_socials FROM social_types;
SELECT COUNT(*) AS total_gsocials FROM game_socials;

SELECT COUNT(*) AS total_perspectives FROM perspectives;
SELECT COUNT(*) AS total_gperspectives FROM game_perspectives;

SELECT 
    g.title, 
    p.publisher_name, 
    d.company_name AS developer,
    plat.platform_name,
    plat.type
FROM games g
LEFT JOIN publishers p ON g.publisher_id = p.publisher_id
LEFT JOIN game_credits gc ON g.game_id = gc.game_id
LEFT JOIN developers d ON gc.developer_id = d.developer_id
LEFT JOIN game_availability ga ON g.game_id = ga.game_id
LEFT JOIN platforms plat ON ga.platform_id = plat.platform_id
LIMIT 10;

SELECT * FROM three_game_pillars LIMIT 10;

SELECT * FROM games;
SELECT * FROM publishers;
SELECT * FROM developers;
SELECT * FROM platforms;

SELECT * FROM prices;
SELECT * FROM dlcs;
SELECT * FROM deal_prices;

SELECT * FROM game_credits;
SELECT * FROM game_availability;

SELECT * FROM genres;
SELECT * FROM game_genres;

SELECT * FROM social_types;
SELECT * FROM game_socials;

SELECT * FROM perspectives;
SELECT * FROM game_perspectives;




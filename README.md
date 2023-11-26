# Counter-Strike 1.6 Gungame Mode Project


## **CONTEXT**
Counter-Strike (publicly known as Counter-Strike 1.6) is a multiplayer first-person shooter video game (either LAN or online).
The game has two teams that allow you to have a good experience in the game, these are the anti-terrorists and terrorists. The main objective in the game is to take out the enemy (Terrorists) as well as rescue hostages, prevent them from planting an explosive, and in case it has already been planted, defuse it.
Over the years, the game has seen a lot of modifications, one of which is the GunGame (GG) modification. GunGame is a game mode where players progress through a series of weapons by getting a kill with each one. It's a fast-paced and exciting game mode that is popular among Counter-Strike players.
In GunGame, each player starts with a basic weapon, usually a pistol. The objective of the game is to progress through the weapons by getting a kill with each one. When a player gets a kill with a weapon, they automatically advance to the next weapon in the list. The weapons in the list are usually arranged in order of difficulty, with the more challenging weapons coming later in the list.
The game continues until a player gets a kill with the final weapon in the list, which is usually a knife or grenade. The player who gets the final kill wins the game. It's a simple yet exciting game mode that can be played with any number of players.

## **PROJECT SUMMARY**
This project deals with the extraction(daily), transformation, and manipulation of data from a web page of a leaderboard of a Counter-Strike 1.6 game server (Game mode: Gungame). This data is then used for the development of a new leaderboard derived from the original one, generating a new ranking system based on statistical calculations to help in-game decision-making, such as team building for in-game tournaments, analysis and improvement of individual in-game performance, analysis and identification of player behavior patterns, etc.


## TOOLS USED
- Python: ETL - Extraction(Web Scrapping with BeautifulSoup), transformation(Pandas), and loading(Sqlite3).
* SQL: SQLite Database for storage, query development, and data modeling.
+ Windows file system for file back-ups and documentation.
* Windows Task Scheduler for process automation.

## PROJECT WALKTHROUGH

Data Flow Diagram:

![Data Flow Diagram](https://github.com/tomiproyectx/CS1.6GG/blob/main/DFD%20Diagram%20CS16GGTP.png)


[Data Modelling Doc(Technical Design - GGXA.xlsx)](https://github.com/tomiproyectx/CS1.6GG/raw/main/Technical%20Design%20-%20GGXA.xlsx)

**ETL**: Only one [Python script](https://github.com/tomiproyectx/CS1.6GG/blob/main/web_scrapper.py) is in charge of doing all the ETL/ELT processes. It runs daily at midnight on my personal Windows computer (I used Windows Task Scheduler for this). The script extracts the raw data from the corresponding web page(s), cleans it, backs it up locally into a file system, and ingests it through a .csv file into an SQLite database located locally in the same directory as the script.                                                 
Data is ingested into a database table which will contain the raw data with no transformations.
Create Statement for the table: [CREATE TABLE raw_gg_teamplay_players.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/CREATE%20TABLE%20raw_gg_teamplay_players.sql)

Data from the web page(s) is updated in real-time, so the data ingested into the database corresponds to the previous day's batch, with the latest snapshot of the position table.
“fecha_proceso”: This is a piece of data that the script creates at the time of ingestion. It is the date on which the data has been processed by the script.

Raw table sample data:

![Raw table sample data](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/81d8c134-e38c-4f2f-be07-83bb19e458fc)

Then the same script executes a SQLite query that takes care of cleaning (transforming) the raw data already ingested into the database and inserting it into a new table: [INSERT INTO cur_gg_teamplay_players.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/INSERT%20INTO%20cur_gg_teamplay_players.sql)

This SQL query has a logic applied so that only new items are inserted in this new table, thus avoiding ingesting repetitive data from players who have not played the previous day or in previous days.

Sample of transformed data:

![Data cleaned sample data](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/89a0e7c6-8643-4a1f-9265-7e485bd9db44)

As you see, this leaderboard is ranked on player points, which players gain when they kill, assist or win a game. The data shows that the player with more time played than other players tends to have a better position than those players. (Like player in position 1 that has almost doubled the time played and points of the top 5 players).

At this point, the data is ready to be used for the purpose of the project.

**ABT**: An analytical base table is made by querying the data in SQLite, showing the rating of each player based on a calculation(defined by me) using the already transformed data. This calculation uses player performance with the purpose of showing off the impact that each individual player has. [abt_gg_teamplay_data.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/abt_gg_teamplay_data.sql)

rating = ( (shot_acc_ratio . 0,25) + headshot_acc_ratio + (kda . 10) + (wph . 3) + dps + (points_per_min . 0,10) ) / 10

- shot_acc_ratio: Shot accuracy ratio, how many effective shots(hits) over 100 shots.
* headshot_acc_ratio: Headshot accuracy ratio, how many headshots over 100 hits.
+ kda: (Kills + Assists) / Deaths.
- wph: How many matches on average the player has won per hour.
* dps: Damage per second.
+ points_per_min: Points per minute.

**ABT** Sample Data:

![image](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/7e0a336a-6b9d-4256-8c0e-8535c8c2347d)

At this point, the **ABT** shows a new leaderboard and a new ranking system based on player performance instead of player points as it was before.

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

![Data Flow Diagram](https://github.com/tomiproyectx/CS1.6GG/blob/main/DFD%20Diagram%20CS16GGTP%20V2.png)


[Data Modelling Doc(Technical Design - GGXA.xlsx)](https://github.com/tomiproyectx/CS1.6GG/raw/main/Technical%20Design%20-%20GGXA.xlsx)

Only one [Python script](https://github.com/tomiproyectx/CS1.6GG/blob/main/web_scrapper.py) is in charge of doing all the ETL/ELT processes. It runs daily at midnight on my personal Windows computer (I used Windows Task Scheduler for this). The script extracts the raw data from the corresponding web page(s), cleans it, backs it up locally into a file system, and ingests it through a .csv file into an SQLite database located locally in the same directory as the script.                                                 
Data is ingested into a database table which will contain the raw data with no transformations. Following the zone modeling, it ends up being a raw table (RAW)

**RAW Create Statement:** [CREATE TABLE raw_gg_teamplay_players.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/CREATE%20TABLE%20raw_gg_teamplay_players.sql)

Data from the web page(s) is updated in real-time, so the data ingested into the database corresponds to the previous day's batch, with the latest snapshot of the position table.\

Sample data **raw_gg_teamplay_players**:

![raw_gg_teamplay_players](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/5eaf038a-3dee-40b7-a458-c2ab5241aff1)

**“fecha_proceso”**: This is a piece of data that the script creates at the time of ingestion. It is the date on which the data has been processed by the script.

Then the same script executes a SQLite query that takes care of cleaning (transforming) the raw data already ingested into the database and inserting it into a new table. Following the zone modeling, it ends up being a curated table (CUR)

**CUR Insert Statement:** [INSERT INTO cur_gg_teamplay_players.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/INSERT%20INTO%20cur_gg_teamplay_players.sql)

Sample data **cur_gg_teamplay_players**:

![cur_gg_teamplay_players](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/8e6d20e7-43dd-4e82-9718-12f7eb253d23)

This SQL query has a logic applied so that only new items are inserted in this new table(snapshot) for each **fecha_proceso**, thus avoiding ingesting repetitive data from players who have not played the previous day or in previous days.

At this point, the data is ready to be used for the purpose of the project.


As you see in the previous image, this leaderboard is ranked on player points(cur_gg_teamplay_players.POINTS), which players gain when they kill, assist, or win a game. The data shows that the player with more time played than other players tends to have a better position than those players. (Like player in position 1 that has almost doubled the time played and points of the top 5 players). Therefore, it is not possible to see exactly what the impact of each player is on the game.
So I created an analytical base table by querying the data from **cur_gg_teamplay_players** table, showing the rating of each player based on a calculation(defined by me). This calculation uses player performance to show off the impact that each player has on the game, instead of the original data. 

**Building the analytical base table:**\
For this process, I created 3 views in SQLite, each with different calculated variables, and then join the result of these views in a query that inserts into the final table **abt_gg_teamplay_players**. Following the zone modeling, it ends up being a refined table (REF).

[current_month_v.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/current_month_v.sql)
- The most important one, it re-ranks the players based on a pre-defined calculation, which then turns into a classification(abt_gg_teamplay_players.CALIFICACION) number for each player.

[history_v.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/history_v.sql)
- This one shows the past(up to 3 months) performance of each player of certain gameplay variables, such as DPS, wins per hour, etc.

[hjum_v.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/hjum_v.sql)
- This one shows the average number of hours played for each player in the current month.

**REF Insert Statement:** [abt_gg_teamplay_data.sql](https://github.com/tomiproyectx/CS1.6GG/blob/main/abt_gg_teamplay_data.sql)

**abt_gg_teamplay_data.CALIFICACION** Calculation (See [Data Modelling Doc(Technical Design - GGXA.xlsx)](https://github.com/tomiproyectx/CS1.6GG/raw/main/Technical%20Design%20-%20GGXA.xlsx) for more detailed info; metadata, data types, etc.)


	shot_acc_ratio * 0.5                                                                     +

	headshot_acc_ratio * 3                                                                   + 

  	kda * 10                                                                                 + 

  	dmg_done / ( days_played * 24 * 60 * 60 + hours_played * 60 * 60 + minutes_played * 60 ) + 

  	( points / ( hours_played * 60 + days_played * 24 * 60 + minutes_played ) ) * 0.5        +

  	( kills / ( hours_played * 60 + days_played * 24 * 60 + minutes_played ) ) * 0.5
   	__________________________________________________________________________________________
						  10
	


Sample Data **abt_gg_teamplay_data**:

![abt_gg_teamplay_data](https://github.com/tomiproyectx/CS1.6GG/assets/102128738/93449daf-9a5e-49a0-adeb-7cfdc06d1743)

Data from this table always shows the current snapshot of each player, only adding new ones and updating pre-existing records.

At this point, the data shows a new leaderboard and a new ranking system based on player performance instead of player points as it was before.
Moving on, with this data you can analyze player performance and make metrics around it. This would help community players improve their performance and in-game decisions, as well as make tournaments more accurate when pre-selecting players, boosting competitiveness.

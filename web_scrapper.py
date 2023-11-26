# Importing libraries
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import date, timedelta
import sqlite3
import concurrent.futures
import timeit
import time
import logging
import os
import sys

# Defining functions
def fetch(url):
    response = requests.get(url)
    return response.content

def cfDecodeEmail(encodedString):
    r = int(encodedString[:2],16)
    email = ''.join([chr(int(encodedString[i:i+2], 16) ^ r) for i in range(2, len(encodedString), 2)])
    return email


# Defining variables
values = []
variables = ["POSITION","CS_NICK","POINTS","GAMES_WON","KILLS","ASSISTS","DEATHS","HS","HITS","SHOTS","ACCUARACY","DAMAGE","TIME_PLAYED",'fecha_proceso'] # Defining table variables/columns
today = date.today()
yest = date.today() - timedelta(days=1)
yest = yest.strftime("%Y%m%d")
year = yest[0:4]
month = yest[4:6]
urls = []
position = 1

original_stdout = sys.stdout

f = open(fr'C:\Users\tomas\Downloads\GG_TEAMPLAY_DATA\script_log\log_{today.strftime("%Y%m%d")}.txt', 'w')

sys.stdout = f



# Generating request from the first web page to find the amount of pages to be scrapped
first_page = 'https://xa-cs.com.ar/servidores/ranking-1-gungame-teamplay/general/0/'


response = requests.get(first_page)

if response.status_code == 200:
    content = response.content
else:
    logging.basicConfig(level=logging.INFO, 
                        filename=fr'C:\Users\tomas\Downloads\GG_TEAMPLAY_DATA\errors\log_{today.strftime("%Y%m%d")}.log', 
                        filemode='a', 
                        format='%(name)s - %(levelname)s - %(message)s')
    logging.error(f'Error: {response.status_code} ({first_page} does not exist)')
    exit()



soup = BeautifulSoup(content, 'html.parser')



# Scrapping data

pages = int(soup.find('ul',{'class':'ipsPagination'})['data-pages'])

for i in range(1,pages):

    if i == 1:
        url = 'https://xa-cs.com.ar/servidores/ranking-1-gungame-teamplay/general/0/'
        urls.append(url)
    else:
        url = f'https://xa-cs.com.ar/servidores/ranking-1-gungame-teamplay/general/0/page/{i}/'
        urls.append(url)

start_time = timeit.default_timer()

print(f'Extracting data from {pages} pages...')

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(fetch, urls)

i = 0

for result in results:
    soup = BeautifulSoup(result, 'html.parser')
    print(f'Extracting data from page: {urls[i]}')
    table = soup.find('table', {'class': 'ipsTable ipsTable_responsive ipsTable_zebra'})
    i += 1
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) > 0:
            if cells[1].a:
                player = cfDecodeEmail(cells[1].a['data-cfemail']) + cells[1].get_text().strip().replace('[email\xa0protected]','')
            else:
                player = cells[1].text.strip()
            points = cells[2].text.strip()
            wins = cells[3].text.strip()
            frags = cells[4].text.strip()
            assist = cells[5].text.strip()
            deaths = cells[6].text.strip()
            hs = cells[7].text.strip()
            hits = cells[8].text.strip()
            shots = cells[9].text.strip()
            accuracy = cells[10].text.strip()
            damage = cells[11].text.strip()
            time_played = cells[12].text.strip()
            values.append([position,player,points,wins,frags,assist,deaths,hs,hits,shots,accuracy,damage,time_played,yest])
            position += 1

end_time = timeit.default_timer()


print("Tiempo de ejecución: ", end_time - start_time, " segundos")

# Making the dataframe
gungame_teamplay_data = pd.DataFrame(values, columns=variables)


# Saving dataframe into a csv for back-up

path = fr'C:\Users\tomas\Downloads\GG_TEAMPLAY_DATA\raw_gg_teamplay_players\{year}\{month}'

if not os.path.exists(path):
    os.makedirs(path)

gungame_teamplay_data.to_csv(fr'{path}\raw_gg_teamplay_players_{yest}.csv',sep='|',index=False)

# Inserting values into a Sqlite Database
conn = sqlite3.connect('GG_TEAMPLAY_PLAYERS.db')
cursor = conn.cursor()


gungame_teamplay_data.to_sql('raw_gg_teamplay_players', conn, if_exists='append', index=False)

print("insert data into raw_gg_teamplay_players...")

time.sleep(2)


# Cleaning and transforming the data

cursor.execute('''
INSERT INTO cur_gg_teamplay_players(position,nickname,points,games_won,kills,assists,deaths,kda,headshots,hits,shots,shot_acc_ratio,headshot_acc_ratio,dmg_done,dmg_per_hit,days_played,hours_played,minutes_played,fecha_proceso)
SELECT
	CAST(raw.POSITION AS INT) AS position,
	raw.CS_NICK AS nickname,
	CAST(REPLACE(raw.POINTS,'.','') AS INT) AS points,
	CAST(raw.GAMES_WON AS INT) AS games_won,
	CAST(REPLACE(raw.KILLS,'.','') AS INT) AS kills,
	CAST(REPLACE(raw.ASSISTS,'.','') AS INT) AS assists,
	CAST(REPLACE(raw.DEATHS,'.','') AS INT) AS deaths,
	ROUND((CAST(REPLACE(raw.KILLS,'.','') AS REAL)+CAST(REPLACE(raw.ASSISTS,'.','') AS REAL))/CAST(REPLACE(raw.DEATHS,'.','') AS REAL),2) AS kda,
	CAST(REPLACE(raw.HS,'.','') AS INT) AS headshots,
	CAST(REPLACE(raw.HITS,'.','') AS INT) AS hits,
	CAST(REPLACE(raw.SHOTS,'.','') AS INT) AS shots,
	CAST(REPLACE(REPLACE(raw.ACCUARACY,',','.'),'%','') AS REAL) AS shot_acc_ratio,
	ROUND((CAST(REPLACE(raw.HS,'.','') AS REAL)*100)/CAST(REPLACE(raw.SHOTS,'.','') AS REAL),2) AS headshot_acc_ratio,
	CAST(REPLACE(raw.DAMAGE,'.','') AS INT) AS dmg_done,
	ROUND(CAST(REPLACE(raw.DAMAGE,'.','') AS REAL)/CAST(REPLACE(raw.HITS,'.','') AS REAL),2) AS dmg_per_hit,
	CASE WHEN INSTR(raw.TIME_PLAYED,'días') != 0 OR INSTR(raw.TIME_PLAYED,'día') != 0 THEN CAST(TRIM(SUBSTR(raw.TIME_PLAYED,1,2)) AS INT) ELSE 0 END AS days_played,
	CASE 
		WHEN INSTR(raw.TIME_PLAYED,'horas') != 0 OR INSTR(raw.TIME_PLAYED,'hora') != 0 THEN
		(CASE 
			WHEN INSTR(raw.TIME_PLAYED,',') != 0 THEN CAST(TRIM(SUBSTR(raw.TIME_PLAYED,INSTR(raw.TIME_PLAYED,',')+1,3)) AS INT) 
			WHEN INSTR(raw.TIME_PLAYED,'días') != 0 OR INSTR(raw.TIME_PLAYED,'día') != 0 THEN CAST(TRIM(SUBSTR(raw.TIME_PLAYED,INSTR(raw.TIME_PLAYED,'y')+1,3)) AS INT)
			ELSE CAST(TRIM(SUBSTR(raw.TIME_PLAYED,1,2)) AS INT)
		END)
		ELSE 0
	END AS hours_played,
	CASE WHEN INSTR(raw.TIME_PLAYED,'minutos') != 0 OR INSTR(TIME_PLAYED,'minuto') != 0 THEN CAST(TRIM(SUBSTR(raw.TIME_PLAYED,INSTR(raw.TIME_PLAYED,'y')+1,3)) AS INT) ELSE 0 END AS minutes_played,
	CAST(raw.fecha_proceso AS INT) AS fecha_proceso
FROM raw_gg_teamplay_players AS raw
LEFT JOIN cur_gg_teamplay_players AS cur
ON
	raw.CS_NICK = cur.nickname AND
	CAST(REPLACE(raw.POINTS,'.','') AS INT) = cur.points AND
	CAST(REPLACE(raw.KILLS,'.','') AS INT) = cur.kills AND
	CAST(REPLACE(raw.ASSISTS,'.','') AS INT) = cur.assists AND
	CAST(REPLACE(raw.DEATHS,'.','') AS INT) = cur.deaths
WHERE raw.fecha_proceso IN (SELECT MAX(fecha_proceso) FROM raw_gg_teamplay_players)
AND	(cur.points IS NULL OR cur.kills IS NULL OR cur.assists IS NULL OR cur.deaths IS NULL)
''')

print("Inserting data into cur_gg_teamplay_players...")

conn.commit()

time.sleep(5)


with open('abt_gg_teamplay_data.sql', 'r') as file:
    abt_gg_teamplay_data = file.read()


cursor.execute("DELETE FROM abt_gg_teamplay_data")
print("TRUNCATING abt_gg_teamplay_data...")
time.sleep(2)


conn.commit()


cursor.execute(abt_gg_teamplay_data)
print("INSERTING data into abt_gg_teamplay_data...")
time.sleep(5)


conn.commit()


conn.close()


sys.stdout = original_stdout

f.close()
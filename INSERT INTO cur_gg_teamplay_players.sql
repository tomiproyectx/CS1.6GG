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
;
CREATE VIEW current_month AS 
WITH last_photo AS (
SELECT
	DISTINCT
	nickname AS nombre_jugador,
	MAX(fecha_proceso) OVER(PARTITION BY nickname) AS fecha_proceso
FROM cur_gg_teamplay_players
WHERE nickname IN (
SELECT DISTINCT nickname 
FROM cur_gg_teamplay_players 
WHERE 
	SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day')) AND 
	((days_played*24)+hours_played) >= 5
)
AND CAST(SUBSTR(fecha_proceso,1,6) AS INT) >= CAST(strftime('%Y',date('now', '-2 month'))||strftime('%m',date('now', '-2 month')) AS INT)
),

yest AS (
SELECT
	nickname AS nombre_jugador,
	ROUND(CAST(games_won AS REAL)/((CAST(minutes_played AS REAL)/60)+CAST(hours_played AS REAL)+CAST(days_played*24 AS REAL)),2) AS partidas_ganadas_por_hora,
	ROUND(CAST(points AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL)),2) AS puntos_por_minuto,
	ROUND(CAST(kills AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL)),2) AS kills_por_minuto,
	kda,
	ROUND(CAST(dmg_done AS REAL) / CAST(((days_played*24*60*60)+(hours_played*60*60)+(minutes_played*60)) AS REAL),2) AS dps,
	ROUND(shot_acc_ratio,2) AS efectividad_disparos,
	ROUND(headshot_acc_ratio,2) AS efectividad_headshots,
	(
	(shot_acc_ratio*0.5) +
	(headshot_acc_ratio*3) +
	(kda*10) +
	CAST(dmg_done AS REAL) / CAST(((days_played*24*60*60)+(hours_played*60*60)+(minutes_played*60)) AS REAL) +
	(CAST(points AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL))*0.5)+
	(CAST(kills AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL))*0.5)
	) / 10
	AS calificacion,
	MAX(cur.fecha_proceso) OVER() AS fecha_actualizacion
FROM cur_gg_teamplay_players AS cur
INNER JOIN last_photo
ON cur.nickname = last_photo.nombre_jugador AND cur.fecha_proceso = last_photo.fecha_proceso
)



SELECT
	RANK() OVER(ORDER BY calificacion DESC) AS position,
	nombre_jugador,
	partidas_ganadas_por_hora,
	puntos_por_minuto,
	kills_por_minuto,
	kda,
	dps,
	efectividad_disparos,
	efectividad_headshots,
	ROUND(calificacion,3) AS calificacion,
	fecha_actualizacion
FROM yest
;


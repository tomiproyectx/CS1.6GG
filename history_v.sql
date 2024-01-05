CREATE VIEW history AS 

WITH yest AS (
SELECT DISTINCT nickname 
FROM cur_gg_teamplay_players 
WHERE 
	SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day')) AND 
	((days_played*24)+hours_played) >= 5
),

ranking AS (
SELECT
	yest.nickname AS nombre_jugador,
	asd.fecha_proceso,
	CASE WHEN asd.ranking IS NULL THEN 0 ELSE asd.ranking END AS ranking
FROM yest
LEFT JOIN (
SELECT
	nickname AS nombre_jugador,
	SUBSTR(fecha_proceso,1,6) AS periodo,
	MAX(fecha_proceso) AS fecha_proceso,
	RANK() OVER(PARTITION BY nickname ORDER BY SUBSTR(fecha_proceso,1,6) DESC) AS ranking
FROM cur_gg_teamplay_players
WHERE CAST(SUBSTR(fecha_proceso,1,6) AS INT) BETWEEN CAST(strftime('%Y',date('now', '-3 month'))||strftime('%m',date('now', '-3 month')) AS INT) AND CAST(strftime('%Y',date('now', '-1 month'))||strftime('%m',date('now', '-1 month')) AS INT)
GROUP BY 1,2
) AS asd
ON yest.nickname = asd.nombre_jugador
),

datos_ult_3meses_1 AS (
SELECT
	r.nombre_jugador,
	COALESCE(cur.kda,0.0) AS kda,
	COALESCE(cur.shot_acc_ratio,0.0) AS efectividad_disparos,
	COALESCE(cur.headshot_acc_ratio,0.0) AS efectividad_headshots,
	COALESCE(CAST(dmg_done AS REAL) / CAST(((days_played*24*60*60)+(hours_played*60*60)+(minutes_played*60)) AS REAL),0.0) AS dps,
	r.ranking,
	r.fecha_proceso AS fecha_actualizacion
FROM ranking AS r
LEFT JOIN cur_gg_teamplay_players AS cur
ON	cur.nickname = r.nombre_jugador AND cur.fecha_proceso = r.fecha_proceso
)


SELECT
	du3m.nombre_jugador,
	SUM(CASE WHEN ranking = 1 THEN kda ELSE 0.0 END) AS kda_mes_1,
	SUM(CASE WHEN ranking = 2 THEN kda ELSE 0.0 END) AS kda_mes_2,
	SUM(CASE WHEN ranking = 3 THEN kda ELSE 0.0 END) AS kda_mes_3,
	ROUND(SUM(CASE WHEN ranking = 1 THEN dps ELSE 0.0 END),2) AS dps_mes_1,
	ROUND(SUM(CASE WHEN ranking = 2 THEN dps ELSE 0.0 END),2) AS dps_mes_2,
	ROUND(SUM(CASE WHEN ranking = 3 THEN dps ELSE 0.0 END),2) AS dps_mes_3,
	SUM(CASE WHEN ranking = 1 THEN efectividad_disparos ELSE 0.0 END) AS efectividad_disparos_mes_1,
	SUM(CASE WHEN ranking = 2 THEN efectividad_disparos ELSE 0.0 END) AS efectividad_disparos_mes_2,
	SUM(CASE WHEN ranking = 3 THEN efectividad_disparos ELSE 0.0 END) AS efectividad_disparos_mes_3,
	SUM(CASE WHEN ranking = 1 THEN efectividad_headshots ELSE 0.0 END) AS efectividad_headshots_mes1,
	SUM(CASE WHEN ranking = 2 THEN efectividad_headshots ELSE 0.0 END) AS efectividad_headshots_mes2,
	SUM(CASE WHEN ranking = 3 THEN efectividad_headshots ELSE 0.0 END) AS efectividad_headshots_mes3
FROM datos_ult_3meses_1 AS du3m
GROUP BY nombre_jugador

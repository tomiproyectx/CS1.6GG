WITH ranking AS (
SELECT
	nickname AS nombre_jugador,
	SUBSTR(fecha_proceso,1,6) AS periodo,
	MAX(fecha_proceso) AS fecha_proceso,
	RANK() OVER(PARTITION BY nickname ORDER BY SUBSTR(fecha_proceso,1,6) DESC) AS ranking
FROM cur_gg_teamplay_players
WHERE nickname IN (SELECT DISTINCT nickname FROM cur_gg_teamplay_players WHERE SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day')) AND ((days_played*24)+hours_played) >= 5)
GROUP BY 1,2
),

datos_ult_3meses_1 AS (
SELECT
	cur.nickname AS nombre_jugador,
	cur.kda,
	cur.shot_acc_ratio AS efectividad_disparos,
	cur.headshot_acc_ratio AS efectividad_headshots,
	(days_played*24)+hours_played+CASE WHEN minutes_played > 30 THEN 1 ELSE 0 END AS q_horas_jugadas,
	CAST(games_won AS REAL)/((CAST(minutes_played AS REAL)/60)+CAST(hours_played AS REAL)+CAST(days_played*24 AS REAL)) AS partidas_ganadas_por_hora,
	CAST(dmg_done AS REAL) / CAST(((days_played*24*60*60)+(hours_played*60*60)+(minutes_played*60)) AS REAL) AS dps,
	CAST(points AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL)) AS puntos_por_minuto,
	r.periodo,
	r.ranking,
	date('now', '-1 day') AS fecha_actualizacion
FROM cur_gg_teamplay_players AS cur
INNER JOIN ranking AS r
ON	cur.nickname = r.nombre_jugador AND cur.fecha_proceso = r.fecha_proceso
WHERE r.ranking <= 3
),

datos_ult_3meses_2 AS (
SELECT 
	*, 
	CASE WHEN ranking = 1 THEN ((efectividad_disparos*0.25)+(efectividad_headshots*2)+(kda*10)+(partidas_ganadas_por_hora*3)+dps+(puntos_por_minuto*0.10))/10 ELSE 0 END AS calificacion
FROM datos_ult_3meses_1
),

hppd AS (
SELECT 
nickname AS nombre_jugador,
(days_played*24)+hours_played+CASE WHEN minutes_played > 30 THEN 1 ELSE 0 END AS q_horas_jugadas, 
IFNULL(LAG((days_played*24)+hours_played) OVER(PARTITION BY nickname ORDER BY fecha_proceso),0) AS asd
FROM cur_gg_teamplay_players
WHERE SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day'))
),


hddp2 AS (
SELECT 
nombre_jugador,
ROUND(AVG(q_horas_jugadas-asd),2) AS avg_horas_jugadas_ult_mes
FROM hppd
GROUP BY nombre_jugador
)

SELECT
	RANK() OVER(ORDER BY calificacion DESC) AS position,
	du3m.nombre_jugador,
	avg_horas_jugadas_ult_mes AS avg_horas_jugadas,
	ROUND(SUM(CASE WHEN ranking = 1 THEN partidas_ganadas_por_hora ELSE 0 END),2) AS partidas_ganadas_por_hora,
	ROUND(SUM(CASE WHEN ranking = 1 THEN puntos_por_minuto ELSE 0 END),2) AS puntos_por_minuto,
	SUM(CASE WHEN ranking = 1 THEN kda ELSE 0 END) AS kda_mes_1,
	SUM(CASE WHEN ranking = 2 THEN kda ELSE 0 END) AS kda_mes_2,
	SUM(CASE WHEN ranking = 3 THEN kda ELSE 0 END) AS kda_mes_3,
	ROUND(SUM(CASE WHEN ranking = 1 THEN dps ELSE 0 END),2) AS dps_mes_1,
	ROUND(SUM(CASE WHEN ranking = 2 THEN dps ELSE 0 END),2) AS dps_mes_2,
	ROUND(SUM(CASE WHEN ranking = 3 THEN dps ELSE 0 END),2) AS dps_mes_3,
	SUM(CASE WHEN ranking = 1 THEN efectividad_disparos ELSE 0 END) AS efectividad_disparos_mes_1,
	SUM(CASE WHEN ranking = 2 THEN efectividad_disparos ELSE 0 END) AS efectividad_disparos_mes_2,
	SUM(CASE WHEN ranking = 3 THEN efectividad_disparos ELSE 0 END) AS efectividad_disparos_mes_3,
	ROUND(SUM(calificacion),2) AS calificacion,
	fecha_actualizacion
FROM datos_ult_3meses_2 AS du3m
INNER JOIN hddp2
ON du3m.nombre_jugador = hddp2.nombre_jugador
GROUP BY du3m.nombre_jugador
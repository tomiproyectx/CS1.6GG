CREATE VIEW hjum AS
WITH hjum AS (
SELECT 
nickname AS nombre_jugador,
(days_played*24)+hours_played+CASE WHEN minutes_played > 30 THEN 1 ELSE 0 END AS q_horas_jugadas, 
IFNULL(LAG((days_played*24)+hours_played) OVER(PARTITION BY nickname ORDER BY fecha_proceso),0) AS asd
FROM cur_gg_teamplay_players
WHERE SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day'))
AND nickname IN (SELECT DISTINCT nickname FROM cur_gg_teamplay_players WHERE SUBSTR(fecha_proceso,1,6) = strftime('%Y',date('now', '-1 day'))||strftime('%m',date('now', '-1 day')) AND ((days_played*24)+hours_played) >= 5)
),


hddp2 AS (
SELECT 
nombre_jugador,
ROUND(AVG(q_horas_jugadas-asd),2) AS avg_horas_jugadas_ult_mes
FROM hjum
GROUP BY nombre_jugador
)


SELECT *
FROM hddp2

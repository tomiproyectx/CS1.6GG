WITH last_photo AS (
SELECT
	nickname,
	MAX(fecha_proceso) AS fecha_proceso
FROM cur_gg_teamplay_players
WHERE fecha_proceso LIKE '202306%'
GROUP BY nickname
),

mayo AS ( 
SELECT
	cur.nickname,
	cur.kda,
	cur.shot_acc_ratio,
	cur.headshot_acc_ratio,
	(cur.days_played*24)+cur.hours_played AS t_hours_played,
	ROUND(CAST(games_won AS REAL)/((CAST(minutes_played AS REAL)/60)+CAST(hours_played AS REAL)+CAST(days_played*24 AS REAL)),2) AS wph,
	ROUND(CAST(dmg_done AS REAL) / CAST(((days_played*24*60*60)+(hours_played*60*60)+(minutes_played*60)) AS REAL),2) AS dps,
	ROUND(CAST(points AS REAL)/(CAST(hours_played*60 AS REAL)+CAST(days_played*24*60 AS REAL)+CAST(minutes_played AS REAL)),2) AS points_per_min,
	cur.fecha_proceso AS last_day_played,
	MAX(cur.fecha_proceso) OVER() AS date_info
FROM cur_gg_teamplay_players AS cur
INNER JOIN last_photo AS lf
ON	cur.nickname = lf.nickname AND cur.fecha_proceso = lf.fecha_proceso
),

a AS (
SELECT 
nickname,
(days_played*24)+hours_played AS t_hours_played, 
IFNULL(LAG((days_played*24)+hours_played) OVER(PARTITION BY nickname ORDER BY fecha_proceso),0) AS asd,
COUNT(nickname) OVER(PARTITION BY nickname) AS q_days_played,
MAX(fecha_proceso) OVER() AS date_info
FROM cur_gg_teamplay_players
WHERE fecha_proceso LIKE '202306%'
),

hppd AS (
SELECT 
nickname,
ROUND((q_days_played*100)/CAST(SUBSTR(date_info,7,2) AS INT),2) AS 'days_played %',
ROUND(AVG(t_hours_played-asd),3) AS hours_played_per_day
FROM a
GROUP BY nickname
),

todo AS (
SELECT 
	RANK() OVER(ORDER BY ((shot_acc_ratio*0.25)+headshot_acc_ratio+(kda*10)+(wph*3)+dps+(points_per_min*0.10))/10 DESC) AS position,
	mayo.nickname,
	[days_played %],
	hours_played_per_day,
	points_per_min,
	wph,
	dps,
	kda,
	shot_acc_ratio AS shot_acc,
	headshot_acc_ratio,
	ROUND(((shot_acc_ratio*0.25)+headshot_acc_ratio+(kda*10)+(wph*3)+dps+(points_per_min*0.10))/10,2) AS rating,
	last_day_played,
	date_info
FROM mayo
INNER JOIN (SELECT * FROM hppd /*WHERE hours_played_per_day >= 0.5 AND [days_played %] >= 30*/) AS hppd
ON mayo.nickname = hppd.nickname
WHERE t_hours_played > 5
)

SELECT *, rating-(SELECT rating FROM todo WHERE position = 1) AS top1_diff
FROM todo
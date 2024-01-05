INSERT OR REPLACE INTO abt_gg_teamplay_data (
position,nombre_jugador,partidas_ganadas_por_hora,puntos_por_minuto,kills_por_minuto,kda,dps,efectividad_disparos,efectividad_headshots,
calificacion,fecha_actualizacion,avg_horas_jugadas_ult_mes,kda_mes_1,kda_mes_2,kda_mes_3,dps_mes_1,dps_mes_2,dps_mes_3,
efectividad_disparos_mes_1,efectividad_disparos_mes_2,efectividad_disparos_mes_3,efectividad_headshots_mes1,
efectividad_headshots_mes2,efectividad_headshots_mes3 )
select
	cm.*,
	hjum.avg_horas_jugadas_ult_mes,
	h.kda_mes_1,
	h.kda_mes_2,
	h.kda_mes_3,
	h.dps_mes_1,
	h.dps_mes_2,
	h.dps_mes_3,
	h.efectividad_disparos_mes_1,
	h.efectividad_disparos_mes_2,
	h.efectividad_disparos_mes_3,
	h.efectividad_headshots_mes1,
	h.efectividad_headshots_mes2,
	h.efectividad_headshots_mes3
from current_month AS cm
INNER JOIN history AS h,hjum
WHERE cm.nombre_jugador = h.nombre_jugador AND cm.nombre_jugador = hjum.nombre_jugador
ORDER BY cm.position
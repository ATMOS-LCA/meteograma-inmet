QUERY_STATIONS = """
SELECT 
    codigo, 
    nome as estacao 
FROM inmet.estacoes
WHERE EXISTS(SELECT 1 FROM inmet.dados_estacoes WHERE estacao = codigo)
ORDER BY nome
"""

QUERY_LAST_PREVISION = """
SELECT data_inicio data FROM inmet.previsao ORDER BY data_inicio DESC;
"""

QUERY_PREVISION_DATA = """
SELECT
            make_timestamp(
                    EXTRACT(YEAR FROM data)::int,
                    EXTRACT(month FROM data)::int,
                    EXTRACT(day FROM data)::int,
                    SUBSTRING(utc, 1, 2)::int,
                    SUBSTRING(utc, 3, 4)::int,
                    0) data,
            round(temperatura::numeric, 2) as temperatura,
            round(umidade_relativa::numeric, 2) as umidade,
            round(precipitacao::numeric, 2) as chuva
        FROM inmet.dados_detalhados_previsao ddp
        INNER JOIN inmet.previsao p on ddp.previsao_id = p.id
        WHERE p.data_inicio = %(start_date)s AND estacao = %(station)s;
"""

QUERY_INMET_DATA = """
    SELECT
        make_timestamp(
                EXTRACT(YEAR FROM data)::int,
                EXTRACT(month FROM data)::int,
                EXTRACT(day FROM data)::int,
                SUBSTRING(utc, 1, 2)::int,
                SUBSTRING(utc, 3, 4)::int,
                0
        ) data,
        temperatura,
        umidade,
        chuva
    FROM inmet.dados_estacoes
    WHERE estacao = %(station)s AND data BETWEEN %(start_date)s AND %(start_date)s::date + INTERVAL '7 DAYS';
"""
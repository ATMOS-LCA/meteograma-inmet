import os
from psycopg2.errors import UniqueViolation
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool
from csv import reader as CsvReader
from datetime import timedelta
from pandas import DataFrame
from database import Database
from time import sleep
from config import get_config
import sys
QUERY_ESTACOES  = """
SELECT replace(lower(nome), ' ', '') nome, codigo FROM inmet.estacoes;
"""

INSERT_ESTACAO = """
INSERT INTO inmet.estacoes (codigo, nome) SELECT CONCAT('U',MAX(SUBSTR(codigo, 2, 4)::int4) + 1), %(cidade)s FROM inmet.estacoes
RETURNING codigo;
"""

INSERT_DADOS_DETALHADOS_PREVISAO = """
INSERT INTO inmet.dados_detalhados_previsao (
    previsao_id, estacao, data, utc, precipitacao, temperatura, umidade_relativa, 
    pressao_superficie, u10m, v10m, vento, vento_dir, fracao_vento, radiacao_oc_inc
) VALUES (
    %(previsao_id)s, %(estacao)s, TO_DATE(%(data)s, 'dd/MM/yyyy'), %(utc)s, %(precipitacao)s, %(temperatura)s, 
    %(umidade_relativa)s, %(pressao_superficie)s, %(u10m)s, %(v10m)s, %(vento)s, 
    %(vento_dir)s, %(fracao_vento)s, %(radiacao_oc_inc)s
) ON CONFLICT (previsao_id, estacao, data, utc) DO UPDATE SET
    precipitacao = EXCLUDED.precipitacao,
    temperatura = EXCLUDED.temperatura,
    umidade_relativa = EXCLUDED.umidade_relativa,
    pressao_superficie = EXCLUDED.pressao_superficie,
    u10m = EXCLUDED.u10m,
    v10m = EXCLUDED.v10m,
    vento = EXCLUDED.vento,
    vento_dir = EXCLUDED.vento_dir,
    fracao_vento = EXCLUDED.fracao_vento,
    radiacao_oc_inc = EXCLUDED.radiacao_oc_inc;
"""

INSERT_DADOS_TEMPERATURA_PREVISAO = """
INSERT INTO inmet.dados_temperatura_previsao (
    previsao_id, estacao, data, temperatura_max, temperatura_min, acumpre, nebulos
) VALUES (
    %(previsao_id)s, %(estacao)s, TO_DATE(%(data)s, 'dd/MM/yyyy'), %(temperatura_max)s, %(temperatura_min)s, %(acumpre)s, %(nebulos)s
) ON CONFLICT (previsao_id, estacao, data) DO UPDATE SET
    temperatura_max = EXCLUDED.temperatura_max,
    temperatura_min = EXCLUDED.temperatura_min,
    acumpre = EXCLUDED.acumpre,
    nebulos = EXCLUDED.nebulos;
"""

INSERT_PREVISAO = """
INSERT INTO inmet.previsao (data_previsao, data_inicio, tamanho_previsao, modelo) VALUES (TO_DATE(%(data)s, 'dd/MM/yyyy'), TO_DATE(%(data)s, 'dd/MM/yyyy'), %(tamanho_previsao)s, %(modelo)s)
ON CONFLICT (data_previsao, tamanho_previsao, modelo) DO UPDATE SET data_inicio = EXCLUDED.data_inicio
RETURNING id;
"""


SEPARADOR = ','
SEARCH_TERM_PREVISAO_TEMPERATURA = ('d7.csv', 'd6.csv', 'd5.csv', 'd4.csv', 'd3.csv', 'd2.csv', 'd1.csv')

def normalize_float(value: str):
    if not value: return None
    return float(value)

def buscar_estacacao(cidade: str, estacoes: DataFrame, db: Database):
    estacao = estacoes[( estacoes['nome'] == cidade.replace(' ', '').lower() )].to_dict('records')
    if (len(estacao) == 0):
        try: 
            estacao = db.execute_query(INSERT_ESTACAO, { 'cidade': cidade })
        except UniqueViolation as e:
            print(f'CONFLICT: {e} \n waiting...')
            sleep(0.1)
            estacao = db.execute_query(INSERT_ESTACAO, { 'cidade': cidade })
        
    return estacao[0]['codigo']

def extrair_dados_previsao_detalhada(caminho_arquivo: Path, estacoes: DataFrame, previsaoId: int):
    try:
        csv : list[list[str]] = []
        with open(caminho_arquivo) as arquivo:
            csv = list(CsvReader(arquivo, delimiter=SEPARADOR))[1:]
        numeroColunas = len(csv[0])
        if not numeroColunas:
            return []
        with Database() as db:
            codigo_estacao = buscar_estacacao(str(caminho_arquivo).split('/')[-1].split('meteogram')[0].replace('_', ' '), estacoes, db)
            dicts = list(map(lambda x: {
            'estacao': codigo_estacao,
            'data': x[0].split(' ')[0],
            'previsao_id': previsaoId,
            'utc': x[0].split(' ')[1],
            'precipitacao': normalize_float(x[1]) if numeroColunas >= 2 else None,
            'temperatura': normalize_float(x[2]) if numeroColunas >= 3 else None,
            'umidade_relativa': normalize_float(x[3]) if numeroColunas >= 4 else None,
            'pressao_superficie': normalize_float(x[4]) if numeroColunas >= 5 else None,
            'u10m': normalize_float(x[5]) if numeroColunas >= 6 else None,
            'v10m': normalize_float(x[6]) if numeroColunas >= 7 else None,
            'vento': normalize_float(x[7]) if numeroColunas >= 8 else None,
            'vento_dir': normalize_float(x[8]) if numeroColunas >= 9 else None,
            'fracao_vento': normalize_float(x[9]) if numeroColunas >= 10 else None,
            'radiacao_oc_inc': normalize_float(x[10]) if numeroColunas >= 11 else None,
            }, csv))
            return dicts
    except Exception as e:
        print(f'Erro ao ler arquivo: {caminho_arquivo}:\n {e}')
        return[]
    
def extrair_dados_previsao_temperatura(caminho_arquivo: Path, previsao: str, estacoes: DataFrame, previsaoId: int):
    try:
        dia_previsao = int(str(caminho_arquivo)[-5]) - 1
        csv : list[list[str]] = []
        with open(caminho_arquivo) as arquivo:
            csv = list(CsvReader(arquivo, delimiter=SEPARADOR))[1:]
        data_previsao = (datetime.strptime(previsao, '%Y%m%d%H') - timedelta(days=dia_previsao)).strftime('%d/%m/%Y')
        with Database() as db:
            return list(map(lambda x: {
            'data': data_previsao,
            'estacao': buscar_estacacao(x[1], estacoes, db),
            'previsao_id': previsaoId,
            'temperatura_max': normalize_float(x[-4]),
            'temperatura_min': normalize_float(x[-3]),
            'acumpre': normalize_float(x[-2]),
            'nebulos': normalize_float(x[-1])
        }, csv))
    except Exception as e:
        print(f'Erro ao ler arquivo: {caminho_arquivo}:\n {e}')
        return[]

def extrair_previsao_retroativo(caminho_previsao, previsao, config, estacoes):
    dataPrevisao = datetime.strptime(previsao[:8], '%Y%m%d').strftime('%d/%m/%Y')
    previsaoId: int = 0
    with Database() as db:
        previsaoId = db.execute_query(INSERT_PREVISAO, { 'data': dataPrevisao, 'tamanho_previsao': 7, 'modelo': 'OMP_4KM'  })[0]['id']
    arquivos_previsao_temperatura = list(map(lambda x: (Path(os.path.join(caminho_previsao, x)), previsao, estacoes, previsaoId), 
                                            filter(lambda x: x.endswith(SEARCH_TERM_PREVISAO_TEMPERATURA), os.listdir(caminho_previsao))))
    arquivos_previsao_detalhada = list(map(lambda x:  (Path(os.path.join(caminho_previsao, x)), estacoes, previsaoId), 
                                filter(lambda x: 
                                    x.endswith(f'{previsao}.csv') and not x.startswith('meteogram_omp_4km'), 
                                    os.listdir(caminho_previsao))))
    dados_previsao_temperatura = []
    dados_previsao_detalhada = []
    for arquivo_previsao_temperatura in arquivos_previsao_temperatura:
        for item in extrair_dados_previsao_temperatura(*arquivo_previsao_temperatura):
            dados_previsao_temperatura.append(item)
            
    for arquivo_previsao_detalhada in arquivos_previsao_detalhada:
        for item in extrair_dados_previsao_detalhada(*arquivo_previsao_detalhada):
            dados_previsao_detalhada.append(item)

    with Database() as db:
        db.execute_command_batch(INSERT_DADOS_TEMPERATURA_PREVISAO, dados_previsao_temperatura)
        db.execute_command_batch(INSERT_DADOS_DETALHADOS_PREVISAO, dados_previsao_detalhada)

def consumir_previsoes_passado():
    config = get_config()
    estacoes : DataFrame = DataFrame()
    with Database() as db:
        estacoes = DataFrame(db.execute_query(QUERY_ESTACOES))
    caminhos_previsoes = list(map(lambda x: 
                                (Path(os.path.join(config['caminho_dados_previsao'], x)), x, config, estacoes), 
                                list(filter(lambda x: x.isnumeric(), os.listdir(config['caminho_dados_previsao'])))))
    with Pool(4) as pool:
        pool.starmap(extrair_previsao_retroativo, caminhos_previsoes)
        

def extrair_previsao():    
    config = get_config()
    dataAtual = datetime.now().strftime('%d/%m/%Y')
    previsoes = list(filter(lambda x: x[:8] == datetime.now().strftime('%Y%m%d'), os.listdir(config['caminho_dados_previsao'])))
    if not previsoes:
        print(f'Previsão não encontrada para {dataAtual}')
        return
    estacoes : DataFrame = DataFrame()
    previsaoId: int = 0
    with Database() as db:
        estacoes = DataFrame(db.execute_query(QUERY_ESTACOES))
        previsaoId = db.execute_query(INSERT_PREVISAO, { 'data': dataAtual, 'tamanho_previsao': 7, 'modelo': 'OMP_4KM'  })[0]['id']
    for previsao in previsoes:
        caminho_previsao = os.path.join(config['caminho_dados_previsao'], previsao)
        
        arquivos_previsao_temperatura = list(map(lambda x: (Path(os.path.join(caminho_previsao, x)), previsao, estacoes, previsaoId), 
                                                filter(lambda x: x.endswith(SEARCH_TERM_PREVISAO_TEMPERATURA), os.listdir(caminho_previsao))))
        arquivos_previsao_detalhada = list(map(lambda x:  (Path(os.path.join(caminho_previsao, x)), estacoes, previsaoId), 
                                    filter(lambda x: 
                                        x.endswith(f'{previsao}.csv') and not x.startswith('meteogram_omp_4km'), 
                                        os.listdir(caminho_previsao))))
        dados_previsao_temperatura = []
        dados_previsao_detalhada = []
        with Pool(3) as pool:
            results_temperatura = pool.starmap(extrair_dados_previsao_temperatura, arquivos_previsao_temperatura)
            dados_previsao_temperatura = [item for sublist in results_temperatura for item in sublist]
            results_detalhado = pool.starmap(extrair_dados_previsao_detalhada, arquivos_previsao_detalhada)
            dados_previsao_detalhada = [item for sublist in results_detalhado for item in sublist]
        
        with Database() as db:
            db.execute_command_batch(INSERT_DADOS_TEMPERATURA_PREVISAO, dados_previsao_temperatura)
            db.execute_command_batch(INSERT_DADOS_DETALHADOS_PREVISAO, dados_previsao_detalhada)

def main():
    if '--retroativo' in sys.argv:
        consumir_previsoes_passado()
        return
    extrair_previsao()


main()
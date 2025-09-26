#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author VB Capistrano
@date 2019-06-10
@brief Meteogram for WRF 3-days-simulation (MS State)
'''

import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
import sys
import glob
import os
import pandas as pd
import matplotlib.ticker as mticker
import psycopg2
from   metpy.calc import wind_direction


DB_CONN_STR = "dbname=postgres user=postgres password=atmos2025 host=34.39.143.242 port=5432"

def get_db_connection():
    return psycopg2.connect(DB_CONN_STR)


plt.close()
date = sys.argv[1]
hour = sys.argv[2]

odir = "./plot/%s%s/" % (date, hour)
if not os.path.isdir(odir):
    os.mkdir(odir)

fdir = "./datain/%s%s/" % (date, hour)
flist = glob.glob(os.path.join(fdir, '*d02*'))

dados_estacoes = pd.read_csv('Coodernadas_MS.csv', sep=',')

dset = xr.open_dataset(flist[0])

KELVIN_BASIS = 273.15

# Variáveis meteorológicas
precc = dset['RAINC']  # precipitação convectiva cumulativa
precsh = dset['RAINSH']  # precipitação total acumulada em escala de grade
precnc = dset['RAINNC']  # precipitação cumulativa não convectiva
t2 = dset['T2'] - KELVIN_BASIS  # Temperatura em °C
q2 = dset['Q2']  # Umidade específica (kg/kg)
ps = dset['PSFC'] / 100  # Pressão superficial em hPa
v10 = dset['V10']  # Componente V do vento a 10m
u10 = dset['U10']  # Componente U do vento a 10m
cld = dset['CLDFRA']  # Fração de nebulosidade
swd = dset['SWDOWN']  # Radiação solar de onda curta incidente (W/m²)
time = dset['Times']
lat = dset.coords['XLAT']
lon = dset.coords['XLONG']
prec = precc + precsh + precnc  # Precipitação total

lat1d=lat.values[0,:,0]
lon1d=lon.values[0,0,:]

dlat=lat1d[1]-lat1d[0]
dlon=lon1d[1]-lon1d[0]

# Configuração do formato de exibição
pd.options.display.float_format = '{:.2f}'.format
pd.set_option('display.max_columns', None)

for j in range(len(dados_estacoes['Cidade'])):
    city = dados_estacoes['Cidade'][j]
    llat = float(dados_estacoes['latitude'][j])
    llon = float(dados_estacoes['longitude'][j])
    alt = float(dados_estacoes['altitude'][j])

    idx = {}
    idx['lat'] = (lat1d >= llat - 2 * dlat) & (lat1d <= llat + 2 * dlat)
    idx['lon'] = (lon1d >= llon - 2 * dlon) & (lon1d <= llon + 2 * dlon)
    
    # Extração das variáveis para o ponto de interesse
    precs = prec[:, idx['lat'], idx['lon']]  # Chuva (mm)
    t2s = t2[:, idx['lat'], idx['lon']]  # Temperatura (°C)
    q2s = q2[:, idx['lat'], idx['lon']]  # Umidade específica
    pss = ps[:, idx['lat'], idx['lon']]  # Pressão (hPa)
    v10s = v10[:, idx['lat'], idx['lon']]  # Componente V do vento
    u10s = u10[:, idx['lat'], idx['lon']]  # Componente U do vento
    clds = cld[:, :, idx['lat'], idx['lon']]  # Nebulosidade
    swds = swd[:, idx['lat'], idx['lon']]  # Radiação solar (W/m²)
    
    # Cálculos derivados
    dirs = wind_direction(u10s, v10s, convention='from')  # Direção do vento
    vel_vento = 3.6 * np.sqrt(u10s**2 + v10s**2)  # Velocidade do vento em km/h
    
    # Cálculo da precipitação horária
    precsr = np.zeros(precs.shape)
    precsr[0] = np.nan
    for i in range(len(time) - 1):
        precsr[i + 1] = precs[i + 1] - precs[i]
        
    # Cálculo da umidade relativa (%)
    RH = 26.3 * pss * q2s / (np.exp(17.67 * (t2s + 273.15 - 273.16) / (t2s + 273.15 - 29.65)))
    
    # Cálculo da pressão ao nível da estação (hPa)
    Po = pss * (1 - 0.0065 * alt / (t2s + 0.0065 * alt + 273.15))**(-5.257)

    # Criação do DataFrame com dados resumidos
    summary_data = {
        'Data': [time.values[0][:19].decode('utf-8')],
        'Cidade': [city],
        'Latitude': [llat],
        'Longitude': [llon],
        'Altitude': [alt],
        'Temp_Max_C': [np.max(np.mean(t2s, axis=(1, 2)))],
        'Temp_Min_C': [np.min(np.mean(t2s, axis=(1, 2)))],
        'Prec_Acum_mm': [np.sum(np.mean(precsr, axis=(1, 2)))],
        'UR_Media_%': [np.mean(np.mean(RH, axis=(1, 2)))],
        'Pressao_Media_hPa': [np.mean(np.mean(Po, axis=(1, 2)))],
        'Vel_Vento_Media_km_h': [np.mean(np.mean(vel_vento, axis=(1, 2)))],
        'Radiacao_Media_W_m2': [np.mean(np.mean(swds, axis=(1, 2)))],
        'Nebulosidade_Media_%': [np.mean(np.mean(clds, axis=(1, 2, 3))) * 100]
    }

    df_summary = pd.DataFrame(summary_data)

    # Salva o arquivo CSV formatado
    csv_path = os.path.join(odir, f"{city.replace(' ', '_')}_resumo_meteorologico.csv")
    df_summary.to_csv(csv_path, index=False, sep=',', encoding='utf-8')

    # Gera também o arquivo completo com todas as horas
    full_data = {
        'Data': [t.decode('utf-8') for t in time.values],
        'Chuva_mm': np.mean(precsr, axis=(1, 2)),
        'Temperatura_C': np.mean(t2s, axis=(1, 2)),
        'Umidade_Relativa_%': np.mean(RH, axis=(1, 2)),
        'Pressao_hPa': np.mean(Po, axis=(1, 2)),
        'Velocidade_Vento_km_h': np.mean(vel_vento, axis=(1, 2)),
        'Direcao_Vento_graus': np.mean(dirs, axis=(1, 2)),
        'Radiacao_W_m2': np.mean(swds, axis=(1, 2)),
        'Nebulosidade_%': np.mean(clds, axis=(2, 3))[:, 0] * 100  # Nebulosidade no nível mais baixo
    }

    df_full = pd.DataFrame(full_data)
    full_csv_path = os.path.join(odir, f"{city.replace(' ', '_')}_dados_completos.csv")
    df_full.to_csv(full_csv_path, index=False, sep=',', encoding='utf-8')

    print(f"\n{'=' * 50}")
    print(f"Dados meteorológicos para {city}")
    print(f"Arquivo resumo salvo em: {csv_path}")
    print(f"Arquivo completo salvo em: {full_csv_path}")
    print("Resumo dos dados:")
    print(df_summary.to_markdown())
    print(f"{'=' * 50}\n")

    # Limpeza de memória
    del precs, t2s, q2s, pss, v10s, u10s, clds, swds, precsr, RH, Po, dirs, vel_vento
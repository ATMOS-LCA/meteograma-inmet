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
from metpy.calc import wind_direction

plt.close()
date=sys.argv[1]
hour=sys.argv[2]
print(date,hour)

odir="C:\\IC\\wrf\\plot\\%s%s\\"%(date,hour)
if not os.path.isdir(odir):
    os.mkdir(odir)

fdir="C:\\IC\\wrf\\datain\\%s%s\\"%(date,hour)
flist=glob.glob(os.path.join(fdir,'*d02*'))

data = pd.read_csv('Coodernadas_MS.csv',sep=',')

dset = xr.open_dataset(flist[0])

precc  = dset['RAINC']
precsh = dset['RAINSH']
precnc = dset['RAINNC']
t2 = dset['T2']-273.15
q2 = dset['Q2']
ps = dset['PSFC']/100
v10 = dset['V10']
u10 = dset['U10']
cld = dset['CLDFRA']
swd = dset['SWDOWN']
time = dset['Times'] 
lat  = dset.coords['XLAT']
lon  = dset.coords['XLONG']
prec = precc+precsh+precnc

# Configuração do formato de exibição
pd.options.display.float_format = '{:.2f}'.format
pd.set_option('display.max_columns', None)

for j in range(len(data['Cidade'])):
    city=data['Cidade'][j]
    llat=float(data['latitude'][j])
    llon=float(data['longitude'][j])
    alt =float(data['altitude'][j])

    idx={}
    idx['lat'] = (lat1d >= llat-2*dlat) & (lat1d <= llat+2*dlat)
    idx['lon'] = (lon1d >= llon-2*dlon) & (lon1d <= llon+2*dlon)
    
    precs = prec[:,idx['lat'],idx['lon']]
    t2s   = t2[:,idx['lat'],idx['lon']]
    q2s   = q2[:,idx['lat'],idx['lon']]
    pss   = ps[:,idx['lat'],idx['lon']]
    v10s  = v10[:,idx['lat'],idx['lon']]
    u10s  = u10[:,idx['lat'],idx['lon']]
    clds  = cld[:,:,idx['lat'],idx['lon']]
    swds  = swd[:,idx['lat'],idx['lon']]
    
    dirs = wind_direction(u10s, v10s, convention='from')
    precsr=np.zeros(precs.shape)
    precsr[0]=np.nan
    for i in range(len(time)-1):
        precsr[i+1]=precs[i+1]-precs[i]
        
    RH = 26.3*pss*q2s/(np.exp(17.67*(t2s+273.15-273.16)/(t2s+273.15-29.65)))
    Po = pss*(1-0.0065*alt/(t2s+0.0065*alt+273.15))**(-5.257)

    # Criação do DataFrame com dados resumidos
    summary_data = {
        'Data': [time.values[0][:19].decode('utf-8')],
        'Cidade': [city],
        'Latitude': [llat],
        'Longitude': [llon],
        'Altitude': [alt],
        'Temp_Max': [np.max(np.mean(t2s, axis=(1,2)))],
        'Temp_Min': [np.min(np.mean(t2s, axis=(1,2)))],
        'Prec_Acum': [np.sum(np.mean(precsr, axis=(1,2)))],
        'UR_Media': [np.mean(np.mean(RH, axis=(1,2)))],
        'Pressao_Media': [np.mean(np.mean(Po, axis=(1,2)))],
        'Nebulosidade_Media': [np.mean(np.mean(clds, axis=(1,2,3)))]
    }

    df_summary = pd.DataFrame(summary_data)

    # Salva o arquivo CSV formatado
    csv_path = os.path.join(odir, f"{city.replace(' ', '_')}_resumo_meteorologico.csv")
    df_summary.to_csv(csv_path, index=False, sep=',', encoding='utf-8')

    # Gera também o arquivo completo com todas as horas
    full_data = {
        'Data': [t.decode('utf-8') for t in time.values],
        'Precipitacao': np.mean(precsr, axis=(1,2)),
        'Temperatura': np.mean(t2s, axis=(1,2)),
        'Umidade_Relativa': np.mean(RH, axis=(1,2)),
        'Pressao': np.mean(Po, axis=(1,2)),
        'Velocidade_Vento': 3.6*np.mean(np.sqrt(u10s**2+v10s**2), axis=(1,2)),
        'Direcao_Vento': np.mean(dirs, axis=(1,2)),
        'Nebulosidade': np.mean(clds, axis=(2,3))[:,0]  # Nebulosidade no nível mais baixo
    }

    df_full = pd.DataFrame(full_data)
    full_csv_path = os.path.join(odir, f"{city.replace(' ', '_')}_dados_completos.csv")
    df_full.to_csv(full_csv_path, index=False, sep=',', encoding='utf-8')

    print(f"\n{'='*50}")
    print(f"Dados meteorológicos para {city}")
    print(f"Arquivo resumo salvo em: {csv_path}")
    print(f"Arquivo completo salvo em: {full_csv_path}")
    print("Resumo dos dados:")
    print(df_summary.to_markdown())
    print(f"{'='*50}\n")

    # Limpeza de memória
    del precs, t2s, q2s, pss, v10s, u10s, clds, swds, precsr, RH, Po, dirs

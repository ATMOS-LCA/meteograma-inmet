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

plt.close()
date=sys.argv[1]
hour=sys.argv[2]

#odir='/home/mpiuser/cloud/wrf/plot/%s%s/'%(date,hour)
odir="C:\\IC\\wrf\\dataout\\%s%s\\"%(date,hour)
if not os.path.isdir(odir):
    os.mkdir(odir)


#fdir='/home/mpiuser/cloud/wrf/output-omp/%s%s/'%(date,hour)
#flist=glob.glob(os.path.join(fdir,'*d02*4km'))
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
time = dset['Times'] 
lat  = dset.coords['XLAT']
lon  = dset.coords['XLONG']
prec = precc+precsh+precnc

#time axis (solution 1)
hours=[]
for i in range(len(time)):
    hours.append(time.values[i][11:-3])
    
#time axis (solution 2)
times=[]
for i in range(len(time)):
    times.append(time.values[i][8:10].decode('utf-8')+'/'+time.values[i][5:7].decode('utf-8')+' '+time.values[i][11:13].decode('utf-8')+'h')
    
t = np.asarray(times)
   
#time axis (solution 3)
timezone='America/Cuiaba' # this has summer hour 
utc = pd.date_range(start='{0:s} {1:s}'.format(date,hour),periods=len(time),freq='H',tz='Etc/UCT')
ltz = utc.tz_convert(timezone)
ltzf= ltz.strftime("%d/%m %Hh")
y   = np.zeros(ltzf.shape)
    



lat1d=lat.values[0,:,0]
lon1d=lon.values[0,0,:]

dlat=lat1d[1]-lat1d[0]
dlon=lon1d[1]-lon1d[0]

maxtemp = np.zeros(len(data['Cidade']))
mintemp = np.zeros(len(data['Cidade']))
acumpre = np.zeros(len(data['Cidade']))
nebulos  = np.zeros(len(data['Cidade']))


for i in range(7):
    for j in range(len(data['Cidade'])):
        city=data['Cidade'][j]
        llat=float(data['latitude'][j])
        llon=float(data['longitude'][j])
        alt =float(data['altitude'][j])
        #print(j,city,llat,llon,alt)
    
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
        
        
        maxtemp[j]=max(np.mean(t2s[i*24:24+i*24],axis=(1,2)))
        mintemp[j]=min(np.mean(t2s[i*24:24+i*24],axis=(1,2)))
        acumpre[j]=np.mean(precs,axis=(1,2))[(i+1)*24]-np.mean(precs,axis=(1,2))[i*24]
        nebulos[j]=np.mean(clds[0+i*24:24+i*24,:,:,:])
        
    #df.insert(2, "Age", [21, 23, 24, 21], True) 
    
    data.insert(4,"maxtemp",maxtemp,True)
    data.insert(5,"mintemp",mintemp,True)
    data.insert(6,"acumpre",acumpre,True)
    data.insert(7,"nebulos",nebulos,True)
    
    #data.to_csv('{0:s}/meteogram_omp_4km_{1:s}{2:s}_d{3:s}.csv'.format(odir,date,hour,str(i+1)))
    data.to_csv('{0:s}\\meteogram_omp_4km_{1:s}{2:s}_d{3:s}.csv'.format(odir,date,hour,str(i+1)))

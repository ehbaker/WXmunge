'''
  add 1995 -> start of data for Gulkana 1480 and Wolverine 990(from NWIS)
'''

import pandas as pd
import pytz
from settings import Glacier, Station

if Glacier+Station=='Wolverine990':
    start_good_NWIS_data='1997-08-29 04'
    pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"\AllYears\Wx\Raw\telemeteredNWIS\Historical_1995to2017\NWIS_data_" + Glacier + Station+ ".csv"

if Glacier +Station=='Gulkana1480':
   start_good_NWIS_data= '1995-10-03 18'
   pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"/AllYears/Wx/Raw/telemeteredNWIS/" + "NWIS_data_" + Glacier + Station +".csv"

#Read in data
NWISdat=pd.read_csv(pth)

date_format='%Y/%m/%d %H:%M'
timezone='America/Anchorage' #choose from pytz.all_timezones

NWISdat['DateTime']=pd.to_datetime(NWISdat['UTC_time'], format=date_format)
NWISdat['DateTime'].timezone='UTC'

#Round to nearest 15 minutes (transmission/ logger time may not be exactly @ the 15 min)
NWISdat['DateTime']=NWISdat['DateTime'].dt.round('15min')

NWISdat=NWISdat.set_index('DateTime')

#Populate local time column
local_timezone=pytz.timezone(timezone)
NWISdat['local_time'] = NWISdat.index.tz_localize('UTC').tz_convert(local_timezone)


og_pth=r"Q:/Project Data/GlacierData/Benchmark_Program/Data/"+ Glacier + r"/AllYears/Wx/LVL0/emily/" + Glacier.lower() + Station +"_15min_all.csv"
dat=pd.read_csv(og_pth)
dat['DateTime']=pd.to_datetime(dat['UTC_time'], format=date_format)
dat['DateTime'].timezone='UTC'
dat=dat.set_index('DateTime')

#These are the columns present in the main file
out_columns=['UTC_time', 'local_time', 'Tpassive1', 'Tpassive2',
       'TAspirated1', 'TAspirated2', 'RelHum', 'StageCumulative',
       'TPGCumulative', 'WindSpeed', 'WindGustSpeed', 'WindDir', 'Barom',
        'VecAvgWindDir', 'RadiationIn', 'RadiationOut', 'SnowDepth', 'LoggerTemp', 'LoggerBattery']

for col in out_columns:
    if col not in NWISdat.columns:
        NWISdat[col]=pd.np.nan #create the column; fill with NANs

#Find beginning of valid logger data
logger_start=dat.first_valid_index()

NWIS_data_to_add=NWISdat[start_good_NWIS_data:logger_start] #before this, there are only error values recorded by NWIS

AllData=pd.concat([NWIS_data_to_add, dat], axis=0)

#Ensure data is sorted by time
AllData.sort_index(inplace=True)

#Make  index timezone-aware
AllData.index=AllData.index.tz_localize('UTC', ambiguous='infer')

#Set output format of time
AllData['UTC_time']=AllData.index.strftime(date_format)#Create column for true local time (as string, not UTC - X hrs)
AllData['local_time']=AllData.index.tz_convert(timezone).strftime(date_format)#Create column for true local time (as string, not UTC - X hrs)

save_pth=r"Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier+ r"/AllYears/Wx/LVL0/emily/" + Glacier.lower() + Station+"_15min_NWIS_1990s_added.csv"

#columns desired in standard output
out_columns=['UTC_time', 'local_time', 'Tpassive1', 'Tpassive2',
       'TAspirated1', 'TAspirated2', 'RelHum', 'StageCumulative',
       'TPGCumulative', 'WindSpeed', 'WindGustSpeed', 'WindDir', 'Barom',
        'VecAvgWindDir', 'RadiationIn', 'RadiationOut', 'SnowDepth', 'LoggerTemp', 'LoggerBattery']

#If this columns is not in dataframe, create
for col in out_columns:
    if col not in AllData.columns:
        AllData[col]=pd.np.nan #create the column; fill with NANs
        
save_dat=AllData[out_columns]

#Ensure data does not have duplicates
save_dat.drop_duplicates(inplace=True)

save_dat.to_csv(save_pth, index=False, float_format='%g')
print("1990s data added to logger from NWIS at " + Glacier + Station)
print("wrote data to " + save_pth)

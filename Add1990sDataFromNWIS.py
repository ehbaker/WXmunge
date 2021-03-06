'''
  add 1995 -> start of data for Gulkana 1480 and Wolverine 990(from NWIS)
  
  For South Cascade, add whole NWIS archive
'''
import pandas as pd
import pytz
from settings import Glacier, Station
import settings
data_columns, general_data_columns, out_date_format, precip_columns, precip_gage_change, primary_temp_column, temp_columns, timezone, wind_col, wind_dir_columns = settings.get_settings(settings.Glacier, settings.Station)
from settings import base_path
og_pth=r"Q:/Project Data/GlacierData/Benchmark_Program/Data/"+ Glacier + r"/AllYears/Wx/LVL0/" + Glacier.lower() + Station +"_15min_all_LVL0.csv"

work_from_home=True


if Glacier+Station=='Wolverine990':
    start_good_NWIS_data='1997-08-29 04'
    pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"\AllYears\Wx\Raw\telemeteredNWIS\Historical_1995to2017\NWIS_data_" + Glacier + Station+ ".csv"
    logger_data_exists=True
if Glacier +Station=='Gulkana1480':
   start_good_NWIS_data= '1995-10-03 18'
   pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"/AllYears/Wx/Raw/telemeteredNWIS/" + "NWIS_data_" + Glacier + Station +".csv"
   logger_data_exists=True
if Glacier +Station =='SouthCascade1830':
    start_good_NWIS_data='2010-07-09 10'
    pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"/AllYears/Wx/Raw/telemeteredNWIS_hut/" + "NWIS_data_" + Glacier + Station +".csv"
    logger_data_exists=True
    #this is made via Pull_In1990sWxData.ipynb
if Glacier +Station =='SouthCascade1640':
    start_good_NWIS_data='1993-08-24 03'
    pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"/AllYears/Wx/Raw/telemeteredNWIS_gage_SCGMiddleTarn/" + "NWIS_data_" + Glacier + Station +".csv"
    logger_data_exists=False
if Glacier +Station =='Wolverine370':
    start_good_NWIS_data='1997-05-21 10'
    pth="Q:/Project Data/GlacierData/Benchmark_Program/Data/" + Glacier + r"/AllYears/Wx/Raw/telemeteredNWIS/Historical_1997to2017StreamGage/" + "NWIS_data_" + Glacier + Station +".csv"
    logger_data_exists=False

if work_from_home==True:
    if Glacier + Station=='Wolverine990':
        og_pth=r'C:\Users\ehbaker\Documents/BrokenServer/Data/Wolverine/AllYears/Wx/LVL0/wolverine990_15min_all_LVL0.csv'
        pth=r"C:\Users\ehbaker\Documents\BrokenServer\Data\Wolverine\AllYears\Wx\Raw\Telemetered\NWIS_data_Wolverine990.csv"
    if Glacier + Station=='Gulkana1480':
        og_pth=r'C:\Users\ehbaker\Documents/BrokenServer/Data/Gulkana/AllYears/Wx/LVL0/gulkana1480_15min_all_LVL0.csv'
        pth=r"C:\Users\ehbaker\Documents\BrokenServer\Data\Gulkana\AllYears\Wx\Raw\telemeteredNWIS\NWIS_data_Gulkana1480.csv"

#Read in data
NWISdat=pd.read_csv(pth)
#data_cols=NWISdat.columns[~NWISdat.columns.str.contains('time')].tolist() #store names of data columns

date_format='%Y/%m/%d %H:%M'
timezone='America/Anchorage' #choose from pytz.all_timezones

NWISdat['DateTime']=pd.to_datetime(NWISdat['UTC_time'], format=date_format)
NWISdat['DateTime'].timezone='UTC'

#Round to nearest 15 minutes (transmission/ logger time may not be exactly @ the 15 min)
NWISdat['DateTime']=NWISdat['DateTime'].dt.round('15min')

#Drop duplicates where NWIS has stored at the logger time and identically at the telemetered time (maybe ~ 1 min different)
NWISdat=NWISdat.drop_duplicates(subset=['DateTime'], keep='first') #IMPORTANT; here, the first is the good; other telemetered datasets may need different treatment here!!!

NWISdat=NWISdat.set_index('DateTime')

#Populate local time column
local_timezone=pytz.timezone(timezone)
NWISdat['local_time'] = NWISdat.index.tz_localize('UTC').tz_convert(local_timezone)

#Reindex to 15min to ensure no timesteps are skipped
NWISdat=NWISdat.sort_index()
full_range_15_min = pd.date_range(NWISdat.index[0], NWISdat.index[-1], freq='15min')
NWISdat=NWISdat.reindex(index=full_range_15_min, fill_value=pd.np.nan)

#Adjust for stage gage legacy issue in telemetered data 
precip_present=len(precip_columns)>0
if precip_present:
    if 'StageCumulative' in NWISdat.columns:
        NWISdat['StageCumulative']=NWISdat.StageCumulative*5 #legacy issue; see comment above
        print ("adjusted NWIS legacy data by multiplying by 5")

if logger_data_exists:
    dat=pd.read_csv(og_pth)
    dat['DateTime']=pd.to_datetime(dat['UTC_time'], format=date_format)
    dat['DateTime'].timezone='UTC'
    dat=dat.set_index('DateTime')
    
    for col in dat.columns:
        if col not in NWISdat.columns:
            NWISdat[col]=pd.np.nan #create the column; fill with NANs
    
    #Find beginning of valid logger data
    logger_start=dat.first_valid_index()
    
    if not work_from_home:        
        NWIS_data_to_add=NWISdat[start_good_NWIS_data:logger_start] #before this, there are only error values recorded by NWIS
    else:
        NWIS_data_to_add=NWISdat.copy()
        
    AllData=pd.concat([NWIS_data_to_add, dat], axis=0)
else:
    AllData=NWISdat.copy()
    print('No logger data at ' +Glacier + Station)

#Ensure data is sorted by time
AllData.sort_index(inplace=True)

#Make  index timezone-aware
AllData.index=AllData.index.tz_localize('UTC', ambiguous='infer')

#Set output format of time
AllData['UTC_time']=AllData.index.strftime(out_date_format)#Create column for true local time (as string, not UTC - X hrs)
AllData['local_time']=AllData.index.tz_convert(timezone).strftime(out_date_format)#Create column for true local time (as string, not UTC - X hrs)

save_pth=base_path +r"Data/" + Glacier+ r"/AllYears/Wx/LVL0/telemetry_added/" + Glacier.lower()+ Station +"_15min_all_LVL0.csv"

#Ensure data does not have duplicates
save_dat=AllData.drop_duplicates()

#Reorder column
#out_cols=['local_time', 'UTC_time']+temp_columns + precip_columns +[wind_col] +wind_dir_columns + list(set(save_dat.columns) - set(['local_time', 'UTC_time'] + temp_columns + precip_columns +[wind_col] +wind_dir_columns))
save_dat=save_dat[['local_time', 'UTC_time']+data_columns]

save_dat.to_csv(save_pth, index=False, float_format='%g')
print("1990s data added to logger from NWIS at " + Glacier + Station)
print("wrote data to " + save_pth)

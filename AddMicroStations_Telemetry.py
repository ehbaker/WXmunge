# Add telemetered data from MicroStations telemetery#

#Import neccessary libraries
import pandas as pd
from settings import Glacier, Station, base_path

tel_dat=pd.read_csv(base_path+'Data/'+ Glacier+ '/AllYears/Wx/Raw/Telemetered_MicroSpecialties/'+Glacier+Station+'fromMicroSpecialties.csv')
if Glacier =='JuneauIcefield':
   tel_dat.rename(columns={'Date/Time':'DateTime'}, inplace=True)

tel_dat['DateTime']=pd.to_datetime(tel_dat.DateTime, errors='coerce')
tel_dat=tel_dat.dropna(subset=['DateTime'])
tel_dat.set_index('DateTime', inplace=True)
tel_dat=tel_dat.sort_index()

if Station=='Camp17AWS':
    tel_dat['Baro_Kpa']=tel_dat.Baro * 3.38639 #convert telemetered data from in hg to kPa
    tel_dat.drop(['Baro'], axis=1, inplace=True)
if Station=='Camp10AWS':
    tel_dat['Precip_m']=tel_dat['Precip']* 0.0254 #convert inch to meter
    #tel_dat['Precip_m']=tel_dat.Precip_m.cumsum()
    tel_dat.drop(['Precip'], axis=1, inplace=True)

tel_dat_15min=pd.DataFrame()

#Reindex telemetered data from hourly to 15 minute
for col in tel_dat.columns:
    print(col)        
    #Store the locations of NANs
    nan_locations_to_restore=tel_dat[col].isnull().fillna('True')
    nan_locations_to_restore=nan_locations_to_restore.resample('15min').ffill(limit=3).fillna('True') #resample to 15 mins
    
    #Interp to 15 min data
    tel_dat_15min[col]=tel_dat[col].resample('15min').interpolate(method='linear')
    
    #Restore NANs back into timeseries
    nan_locations_to_restore=nan_locations_to_restore.fillna('True')
    nan_locations_to_restore=nan_locations_to_restore.astype(bool)
    tel_dat_15min.loc[nan_locations_to_restore, col]=pd.np.nan

    
tel_dat_15min=tel_dat_15min.reset_index()

tel_dat_long=pd.melt(tel_dat_15min, id_vars=['DateTime'])

#Read in logger data
if Glacier =='JuneauIcefield':
    pth=base_path + "Data/" + Glacier+ "/AllYears/Wx/Raw/" + Glacier+ Station+ "_hourly_all.csv"
    initial_timing='1h'
    
dat=pd.read_csv(pth) #Dat= logger dat

if Glacier =='JuneauIcefield':
   dat.rename(columns={'TIMESTAMP':'DateTime'}, inplace=True)
   
dat.loc[:,'DateTime']=pd.to_datetime(dat['DateTime']) #set to date-time from string
dat['DateTime']=dat['DateTime'].dt.round(initial_timing) #round time to the nearest 5 minute value

#Set time as index
dat=dat.set_index('DateTime')

#Replace NAN with pandas nan (not always automatically done)
dat.replace('NAN', pd.np.NaN, inplace=True)

#Interpolate to 15min
fifteenmin_dat=pd.DataFrame() #create empty dataframe

value_cols=['AirTC_Avg', 'RH', 'WS_ms_S_WVT', 'WindDir_D1_WVT', 'WS_ms_Max',
            'TCDT', 'BP_mbar', 'BP_kPa_Avg', 'NR_Wm2_Avg', 'CNR_Wm2_Avg', 'Rain_in_Tot',
            'BaroInches',	'WindSpMS',	'WindDirDeg',	'WindSpMax', 	'AirTempC',	'RHpercent'] #list of all col names that contain data from loggers

#Reindex to all hourly series to ensure no timesteps are skipped
full_range_hourly = pd.date_range(dat.index[0], dat.index[-1], freq='1H')
dat=dat.reindex(index=full_range_hourly, fill_value=pd.np.nan)
dat.index.name='DateTime'

for col in dat.columns:
    if col not in value_cols:
        print(col)
        print('skipping ' + col)
        continue
        
    #Store the locations of NANs
    nan_locations_to_restore=dat[col].isnull()    
    nan_locations_to_restore=nan_locations_to_restore.resample('15min').ffill(limit=3) #resample to 15 mins
    
    #Interp to 15 min data
    fifteenmin_dat[col]=dat[col].resample('15min').interpolate(method='linear')
    
    #Restore NANs back into timeseries
    nan_locations_to_restore=nan_locations_to_restore.astype(bool)
    fifteenmin_dat.loc[nan_locations_to_restore, col]=pd.np.nan
    
fifteenmin_dat=fifteenmin_dat.reset_index()

#Unit Conversion BS
if 'BP_mbar' in fifteenmin_dat.columns:
    fifteenmin_dat['BP_mbar']= fifteenmin_dat.BP_mbar/10
    
if 'BaroInches' in fifteenmin_dat.columns:
    fifteenmin_dat['BaroInches']= fifteenmin_dat.BaroInches * 3.38639
    
if 'BP_mbar' in fifteenmin_dat.columns:
    fifteenmin_dat['BP_mbar']= fifteenmin_dat.BP_mbar * 0.1
    
if 'Rain_in_Tot' in fifteenmin_dat.columns:
    fifteenmin_dat['Rain_in_Tot']= fifteenmin_dat.Rain_in_Tot * 0.0254


#Reshape so that is in long (v wide) format, to mirror Sutron logger output
fifteenmin_dat_long=pd.melt(fifteenmin_dat, id_vars='DateTime')

fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['AirTC_Avg', 'AirTempC']), 'variable']='AirTemp'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['RH', 'RHpercent']), 'variable']='RH'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['WS_ms_Max', 'WindSpMax']), 'variable']='WindSP_Gust'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['WS_ms_S_WVT']), 'variable']='WindSP'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['WindDir_D1_WVT', 'WindDirDeg']), 'variable']='WindDir_VecAvg'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['BP_kPa_Avg', 'BP_mbar','BaroInches', 'Baro']), 'variable']='Baro_Kpa'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['NR_Wm2_Avg', 'CNR_Wm2_Avg']), 'variable']='SolRad'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['WindSpMS']), 'variable']='WindSpeed'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['Rain_in_Tot']), 'variable']='Precip_m'
fifteenmin_dat_long.loc[fifteenmin_dat_long.variable.isin(['TCDT']), 'variable']='SnowDep1'

alldat=tel_dat_long.append(fifteenmin_dat_long)

print(alldat.variable.unique())

alldat=alldat.drop_duplicates()

alldat.rename(columns={'variable':'Instrument'}, inplace=True)
alldat.rename(columns={'value':'Value'}, inplace=True)


#alldat_wide=alldat.pivot_table(index='DateTime', columns='variable')

out_pth=base_path + "Data/" +Glacier+ "/AllYears/Wx/Raw/" + Glacier.lower()+ Station +"_15min_all.csv"

#alldat_wide=alldat_wide['value'] #strange pivot table thing

alldat['UTC_col']=alldat.DateTime + pd.DateOffset(hours=9)
alldat.sort_index(inplace=True)
alldat.dropna(how='all', inplace=True)
alldat=alldat[alldat.DateTime.notnull()]

alldat.to_csv(out_pth, index=False, date_format='%m/%d/%Y %H:%M:%S')

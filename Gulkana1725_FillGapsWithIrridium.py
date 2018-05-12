'''
  weather station data - fill gaps in Gulkana Nunatak  record (1725) with irridium telemetered data.
    -telemetered data is in english units
    -to be run AFTER L0 but before L1
'''
#Import neccessary libraries
import pandas as pd
import datetime
import glob
#Find all files
fls=glob.glob(r"Q:\Project Data\GlacierData\Benchmark_Program\Data\Gulkana\AllYears\Wx\Raw\telemeteredIrridium\Gulkana*")

#NOTE - ALL must be in same units before appending!!! This should be SI units; request new data download from Irridium if NOT (eg English)

#Append
alldat=pd.DataFrame()
for fl in fls:
    colnmz=pd.read_csv(fl, sep='\t', header=1, nrows=1).columns.str.strip() #colum names (not direcly above data)
    dat=pd.read_csv(fl, sep='\t', header=4, engine='python', names=colnmz) #read in data
    for col in dat:
        dat[col]=dat[col].astype('str').str.strip() #strip whitespace from all columns
    dat=dat.replace('[^\s]([ ]{2,})[^\s]', pd.np.nan, regex=True)
    alldat=alldat.append(dat)
    
#Unique
alldat=alldat.drop_duplicates()
alldat.rename(columns={'Date / Time': 'Date'}, inplace=True) #rename date column
alldat=alldat.reset_index()
#Change name of all data
telemetered_dat=alldat.copy()

#Read in logger data
dat=pd.read_csv("Q:\Project Data\GlacierData\Benchmark_Program\Data\Gulkana\AllYears\Wx\LVL0\gulkana1725_15min_all.csv")
date_format='%Y/%m/%d %H:%M'
date_format_telemetered='%d %b %Y, %H:%M'
out_date_format='%Y/%m/%d %H:%M'
timezone='America/Anchorage' #choose from pytz.all_timezones

dat['DateTime']=pd.to_datetime(dat['UTC_time'], format=date_format)
dat['DateTime'].timezone='UTC'
dat=dat.set_index('DateTime')


#Convert date-time index that contains 24 hours (strptime accepts only 0-23)
bad_midnight_locs=telemetered_dat.Date.str.endswith('24:00') #this is all the places that contain 24hr midnight

telemetered_dat['Day']=telemetered_dat.Date.str.slice(0,2)
telemetered_dat['Month']=telemetered_dat.Date.str.slice(3,6)
telemetered_dat['Time']=telemetered_dat.Date.str.slice(13,18)
telemetered_dat['Year']=telemetered_dat.Date.str.slice(7,11)
telemetered_dat.loc[telemetered_dat.Time=='24:00', 'Time']='00:00' #Change midnight from 24:00 to 0:00, as Python and strftime would expect
telemetered_dat['DateTime']=telemetered_dat.Day + " " + telemetered_dat.Month + " " + telemetered_dat.Year + ", "+ telemetered_dat.Time
telemetered_dat['DateTime']=pd.to_datetime(telemetered_dat.DateTime, format=date_format_telemetered)
telemetered_dat.loc[bad_midnight_locs, 'DateTime']=telemetered_dat.loc[bad_midnight_locs, 'DateTime'] + datetime.timedelta(days=1) #add a day to the 24-hr vs 00  times

telemetered_dat['DateTime']=telemetered_dat.DateTime.dt.round('15min')

telemetered_dat=telemetered_dat.set_index('DateTime')

telemetered_dat.rename(columns = {'GUL Temp-AIR4 DCP-raw':'TAspirated1'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Rad-SOLARDOWN4 DCP-raw':'RadiationIn'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Rad-SOLARUP4 DCP-raw':'RadiationOut'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Dir-WIND4 DCP-raw':'VecAvgWindDir'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Speed-WIND4 DCP-raw':'WindSpeed'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Precip-4 DCP-raw':'TPGCumulative'}, inplace = True)
telemetered_dat.rename(columns = {'GUL Depth-SNOW4 DCP-raw':'SnowDepth'}, inplace = True)

#Convert select items to different units
#Depth - meters to millimeters
for col in ['TPGCumulative', 'SnowDepth']:  
    telemetered_dat[col]= pd.to_numeric(telemetered_dat[col])
    telemetered_dat[col]=telemetered_dat[col]* 0.001


tel_add=telemetered_dat[['TAspirated1', 'RadiationIn', 'RadiationOut', 'VecAvgWindDir', 'WindSpeed', 'TPGCumulative', 'SnowDepth']].copy()

#Replace missing data in manually defined patches (data is missing)
##NOTE - current telemetered data file does NOT include data from 2016/04/30 forward
##IF MORE need to be added in future, just add new pair of Start Gap and End Gap to ends of lists.
Starts_Gaps=['2014/08/24 00:00:00', '2015/04/16 00:00:00', '2015/09/24 00:00:00', '2013/08/27 00:00:00', '2016/08/28 00:00:00']
End_Gaps=['2014/11/14 14:00:00', '2015/05/04 23:00:00', '2016/04/12 23:00:00', '2014/03/18 23:00:00', '2016/12/01 23:00:00']


#For each gap identified and hard-coded above, STORE TELEMETERED DATA
allgapdata=pd.DataFrame()
for xx in range(0,len(Starts_Gaps)):
    telem_gap=tel_add[Starts_Gaps[xx]: End_Gaps[xx]]
    allgapdata=pd.concat([allgapdata, telem_gap])
    
    
#alldat=pd.concat([dat, allgapdata], axis=0) THIS IS MISSING SOME DATA! WTF!!
alldat=dat.append(allgapdata)
alldat.sort_index(inplace=True)
 
#Set output format of time
alldat.index.tz='UTC' #tell pandas what timezone alldat is in

#Sort again
alldat.sort_index(inplace=True)

alldat=alldat[~alldat.index.duplicated(keep='first')] #important to have here; before, earlier in script was dropping too many rows!

alldat['UTC_time']=alldat.index.tz_convert('UTC').strftime(out_date_format)#Create column for true local time (as string, not UTC - X hrs)

alldat['local_time']=alldat.index.tz_convert(timezone).strftime(out_date_format)#Create column for true local time (as string, not UTC - X hrs)

alldat.to_csv(r"Q:/Project Data/GlacierData/Benchmark_Program/Data/Gulkana/AllYears/Wx/LVL0/gulkana1725_15min_all_gaps_filled.csv", index=False, float_format='%g')
print("Gaps in data at Gulkana 1725 filled with Irridium telemetry data")
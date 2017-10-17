'''
  LVL1 WX Cleaning Functions
'''
import numpy as np
import pandas as pd

def isthisworking(): #This is here simply to trouble-shoot importing of the module
    print("Yes it is! Successful import! YAYYYYY!")
    
def remove_malfunctioning_sensor_data(dat, bad_sensor_dates_dat):
    '''
    Function to set bad sensor data to NAN, during specified timeframes. Returns dataframe with NANs in place, and switched values, as indicated with "switch_label"
    dat: dataframe containing data that you are editing. Index MUST BE in local time.
    bad_sensor_dates_dat: dataframe containing sensor name, start/end date of bad sensor data
       
Example table format for bad_sensor_dates_dat:
Sensor	       Start_Date	       End_Date	     Action	       Correct_Label	  Location
------------------------------------------------------------------------------------
TAspirated2	4/25/2014 6:45	9/4/2014 9:00	 switch_label	   TPassive2	     Wolverine990
Tpassive1   	5/7/2013 2:15	   11/6/2013 8:00 	bad		       NAN            Wolverine990

    '''
    for index, row in bad_sensor_dates_dat.iterrows():
        if row['Action']=='bad':
            Start_Date=row['Start_Date']
            End_Date=row['End_Date']
            Sensor=row['Sensor']
            dat.loc[Start_Date:End_Date, Sensor]=np.nan #For dates in this range, set sensor "Sensor" to NAN
        elif row['Action']=='switch_label':
            Start_Date=row['Start_Date']
            End_Date=row['End_Date']
            Sensor=row['Sensor']
            Correct_Label=row['Correct_Label']
            dat.loc[Start_Date:End_Date, Correct_Label]=dat.loc[Start_Date:End_Date, Sensor] #put data in correctly labeled column
            dat.loc[Start_Date:End_Date, Sensor]=np.nan#change the original location to NAN (no data was collected from this sensor)    
            return(dat)
            
def remove_error_temperature_values(temps, low_temp_cutoff, high_temp_cutoff):
    '''
    temps: pandas series of temperatures (NANs OK)
    low_temp_cutoff: numeric value of low cutoff temperature
    high_temp_cutoff: numeric value of high temperature cutoff
    '''
    temps.loc[temps>high_temp_cutoff]=np.nan
    temps.loc[temps<low_temp_cutoff]=np.nan
    return(temps)
    
def hampel(x,k, t0=3):
    '''adapted from hampel function in R package pracma
    x=
    k= number of items in window/2 (# forwarda and backward wanted to capture in median filter)
    '''
    n = len(x)
    y = x #y is the corrected series
    L = 1.4826
    for i in list(range((k + 1),(n - k))):
        if np.isnan(x[(i - k):(i + k)]).all():
            continue
        x0 = np.nanmedian(x[(i - k):(i + k)])
        S0 = L * np.nanmedian(np.abs(x[(i - k):(i + k)] - x0))
        if (np.abs(x[i] - x0) > t0 * S0):
            y[i] = x0
    return(y)
    

def inner_precip_smoothing_func_Nayak2010(precip):
    '''
    precip smoothing routine from Nayak 2010 thesis:
    First 3 records must be >0: check progressively to ensure
    translated from Nayak 2010 thesis; slightly different than Shad's implementation in Matlab.
    Should be run both forward and backwards to smooth data uniformly
    
    precip: 1-d ndarray of numeric, incremental (non-cumulative) precipitation values
    '''  
    
    precip=precip.copy() #avoid modifying original series; make a copy
    precip=pd.Series(precip)
        
    if precip[0]<0:
        precip[1]=precip[1]+precip[0]
        precip[0]=0 #force initial value to 0, if increment is negative
    
    if precip[1]<0:
        if np.nansum(precip[0:3])<0:
            precip[2]=(np.nansum(precip[0:3]))
            precip[0]=0
            precip[1]=0
        else:
            precip[0]=np.nansum(precip[0:3])/3
            precip[1]=precip[0]
            precip[2]=precip[0]
         
    precip[0:3]=precip[0:3] #set values in precip series to the values as edited above; necceary for smoothing
    #Smoothing Loop
    for ii in precip.index[3:-3]:
        #if all NAN in the 5-sample window, skip to next iteration
        if precip.iloc[ii-2:ii+3].isnull().all():
            continue
        if precip[ii]<0:
            check=np.nansum(precip.iloc[ii-2:ii+3])
            if check>=0: #if positive, 5 window values are set to mean of all 5
                precip.iloc[ii-2:ii+3]=np.nanmean(precip.iloc[ii-2:ii+3])
            else:
                precip.iloc[ii+2]=np.nansum(precip.iloc[ii-2:ii+3])
                precip.iloc[ii-2:ii+2]=0
        else:
            precip[ii]=precip[ii]
        
    return(precip)
    
    
def smooth_precip_Nayak2010(dat, dPrecip):
    '''
    Routine for smoothing precipitation data from Nayak 2010 thesis/ 2008 paper.
    Returns dataframe with smoothed precip column (overwrites existing column)
      -relies on inner_precip_smoothing_func_Nayak2010, as included above in this module
    -----
    dat= dataframe, containing weather data.
    dprecip= text; name of column containing the incremental 
    '''
    
    dat2=dat.copy() #copy, to avoid inadvertently altering original dataframe
    #Smooth data in forward direction
    print("smoothing data in forward direction; may take a minute")
    smooth_forward=inner_precip_smoothing_func_Nayak2010(dat2[dPrecip].values)
    print("done with forward smoothing")
    #Smooth Data in backwards direction
    reverse_sorted_data=dat2[dPrecip].copy().sort_index(ascending=False).values
    print("smoothing data in reverse direction; may take a minute")
    smooth_backwards=inner_precip_smoothing_func_Nayak2010(reverse_sorted_data)
    smooth_backwards=smooth_backwards[::-1] #sort forwards again, so in the correct order to store in dataframe
    print('done with backwards')

    #Average
    smooth_forward.index=dat2.index #Reindex in order to add back to original dataframe
    smooth_backwards.index=dat2.index #Reindex in order to add back to original dataframe
    
    dat2['smooth_forward']=smooth_forward      #re-combine into single dataframe
    dat2['smooth_backwards']=smooth_backwards
    dat2['avg']=dat2[['smooth_forward', 'smooth_backwards']].mean(axis=1)
    
    #If first 3 values <0, set to 0. Same with end and last incremental 3 values.
    for ii in range(-3,0):
        if dat2.ix[ii, 'avg']<0:
            dat2.ix[ii, 'avg']=0
    for ii in range(0,3):
        if dat2.ix[ii, 'avg']<0:
            dat2.ix[ii, 'avg']=0   
    
    #Return dataframe with new smoothed precip column
    new_col_name=dPrecip+'_smooth'
    dat[new_col_name]=dat2['avg'].values #overwrite old precip column with new smoothed values
    return(dat)
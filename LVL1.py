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

def remove_error_precip_values_old(precip_cumulative, obvious_error_precip_cutoff, precip_high_cutoff, precip_drain_cutoff):
    '''
    precip_cumulative: pandas series of cumulative precip values; index must be a date-time
    obvious_error_precip_cutoff..: number, giving value that for a 15 minute timestep is obviously an error (unlikely to rain 0.3m in 15 min)
    precip_high_cutoff: 
    precip_drain_cutoff: negative number giving value above which a negative 15 min change is related to station maintenance draining
    '''
    
    #The order of the steps here is very important; as soon as derivative is created and re-summed, loose info on sensor malfunctions
    
    precip_edit=precip_cumulative.copy() #create copy, to avoid inadvertently editing original pandas series
     
    #Step 1 : use incremental precip to set sensor malfunction jumps to NAN in CUMULATIVE timeseres
    dPrecip=precip_edit -precip_edit.shift(1) #create incremental precip timeseries
    for ii in range(0, len(dPrecip)):
        if abs(dPrecip[ii])>obvious_error_precip_cutoff:
            precip_edit[ii]=np.nan
    
    #Step2: remove remaining outliers using one-day (96 samples) median filter
    rolling_median=precip_edit.rolling(96).median().fillna(method='ffill').fillna(method='bfill')
    difference=np.abs(precip_edit - rolling_median)
    threshold=0.2 #threshold for difference between median and the given value
    outlier_idx=difference>threshold
    precip_edit[outlier_idx]=np.nan
    
    #Step3 - remove NANs in cumulative series output by instruments
    precip_edit=precip_edit.interpolate(method='linear', limit=96) #interpolate for gaps < 1 day
    
    #Step4 -recalculate incremental precip, set values outside expected range to 0
    dPrecip=precip_edit -precip_edit.shift(1) #incremental precip
    dPrecip.loc[dPrecip>obvious_error_precip_cutoff]=0
    dPrecip.loc[(dPrecip>precip_high_cutoff) & (dPrecip.index.month>=8) & (dPrecip.index.month<=11)]=0 #set precip refills to 0
    dPrecip.loc[dPrecip<precip_drain_cutoff]=0 #set precip drains to 0
    new_precip_cumulative=dPrecip.cumsum()
    new_precip_cumulative[0]=0 #set beginning equal to 0, not NAN as is created with the cumulative sum
    return(new_precip_cumulative)


def precip_remove_sensor_malfunctions(precip_cumulative, obvious_error_precip_cutoff):
    precip_edit=precip_cumulative.copy()
    #Step 1 : use incremental precip to set sensor malfunction jumps to NAN in CUMULATIVE timeseres
    dPrecip=precip_edit -precip_edit.shift(1) #create incremental precip timeseries
    for ii in range(0, len(dPrecip)):
        if abs(dPrecip[ii])>obvious_error_precip_cutoff:
            precip_edit[ii]=np.nan
    return(precip_edit)

def precip_remove_daily_outliers(precip_cumulative, n=96):
    precip_edit=precip_cumulative.copy()
    #Step2: remove remaining outliers using one-day (96 samples for 15 min data) median filter
    rolling_median=precip_edit.rolling(n).median().fillna(method='ffill').fillna(method='bfill')
    difference=np.abs(precip_edit - rolling_median)
    threshold=0.2 #threshold for difference between median and the given value
    outlier_idx=difference>threshold
    precip_edit[outlier_idx]=np.nan    
    return(precip_edit)
    
def precip_interpolate_gaps_under1day(precip_cumulative, n=96):
    #Step3 - remove NANs in cumulative series output by instruments
    precip_edit=precip_cumulative.copy()
    precip_edit=precip_edit.interpolate(method='linear', limit=96)
    return(precip_edit)
    
def precip_remove_maintenance_noise(precip_cumulative, obvious_error_precip_cutoff, precip_high_cutoff, precip_drain_cutoff):
    '''
    returns incremental precip
    '''
    precip_edit=precip_cumulative.copy()
    dPrecip=precip_edit -precip_edit.shift(1) #incremental precip
    dPrecip.loc[dPrecip>obvious_error_precip_cutoff]=0
    dPrecip.loc[(dPrecip>precip_high_cutoff) & (dPrecip.index.month>=8) & (dPrecip.index.month<=11)]=0 #set precip refills to 0
    dPrecip.loc[dPrecip<precip_drain_cutoff]=0 #set precip drains to 0
    return(dPrecip)
    
def precip_remove_high_frequency_noiseNayak2010(precip_incremental, noise):
    #THIS IS CURRENTLY BROKEN! LAME!!! UGHHH!!
    for ii in range(1, len(precip_incremental)):
        if abs(precip_incremental[ii])>noise:
            jj=ii #create new name for iterator
            for jj in range(ii, len(precip_incremental)):
                newslice=precip_incremental[jj+1:jj+6]
                if(newslice<noise).all():
                    precip_incremental[ii:jj]= (precip_incremental[jj] -precip_incremental[ii])/(jj-ii)
                    print("edited noise at locations " + str(ii) + ":" +str(jj))
                    break #this simple exits the inner loop, continuing the outer
    return(precip_incremental)
                    


def hampel_old_loop(x,k, t0=3):    
    '''adapted from hampel function in R package pracma
    x= 1-d numpy array of numbers to be filtered
    k= number of items in window/2 (# forward and backward wanted to capture in median filter)
    t0= number of standard deviations to use; 3 is default
    '''
    n = len(x)
    y = x #y is the corrected series
    L = 1.4826
    for i in range((k + 1),(n - k)):
        if np.isnan(x[(i - k):(i + k+1)]).all(): #the +1 is neccessary for Python indexing (excludes last value k if not present)
            continue
        x0 = np.nanmedian(x[(i - k):(i + k+1)]) #median
        S0 = L * np.nanmedian(np.abs(x[(i - k):(i + k+1)] - x0))
        if (np.abs(x[i] - x0) > t0 * S0):
            y[i] = x0
    return(y)
    
def hampel(vals_orig, k=7, t0=3):
    '''
    vals: pandas series of values from which to remove outliers
    k: size of window (including the sample; 7 is equal to 3 on either side of value)
    '''
    #Make copy so original not edited
    vals=vals_orig.copy()    
    #Hampel Filter
    L= 1.4826
    rolling_median=vals.rolling(k).median()
    difference=np.abs(rolling_median-vals)
    median_abs_deviation=difference.rolling(k).median()
    threshold= t0 *L * median_abs_deviation
    outlier_idx=difference>threshold
    vals[outlier_idx]=np.nan
    return(vals)
    
def basic_median_outlier_strip(vals_orig, k, threshold):
    vals=vals_orig.copy()
    rolling_median=vals.rolling(k).median()
    difference=np.abs(rolling_median-vals)
    outlier_idx=difference>threshold
    vals[outlier_idx]=np.nan
    return(vals)
    

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
    dprecip= text; name of column containing the incremental precipitation values
    '''
    
    dat2=dat.copy() #copy, to avoid inadvertently altering original dataframe
    #Smooth data in forward direction
    print("  smoothing data in forward direction; may take a minute")
    smooth_forward=inner_precip_smoothing_func_Nayak2010(dat2[dPrecip].values)
    #Smooth Data in backwards direction
    reverse_sorted_data=dat2[dPrecip].copy().sort_index(ascending=False).values
    print("  smoothing data in reverse direction; may take a minute")
    smooth_backwards=inner_precip_smoothing_func_Nayak2010(reverse_sorted_data)
    smooth_backwards=smooth_backwards[::-1] #sort forwards again, so in the correct order to store in dataframe

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
    
def rename_pandas_columns_for_plotting(data_o, desired_columns, append_text):
    '''
    Function that takes dataframe, subsets to desired columns, and renames those columns as indicated.
    For plotting multiple iterations of the same data in a single plot, but with different labels.
    data: dataframe
    desired_columns: list of what columns the text should be appended to
    append_text: text to append to the selected columns
    '''
    data=data_o.copy()
    append_text= append_text
    df=data[desired_columns].copy()
    df=df.add_suffix(append_text)
    return(df)
    
    
    
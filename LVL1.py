'''
  LVL1 WX Cleaning Functions
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    for xx in bad_sensor_dates_dat.index:
    #If sensor data is bad, set to NAN
        if bad_sensor_dates_dat.loc[xx,'Action']=='bad':
            Start_Date=bad_sensor_dates_dat.loc[xx, 'Start_Date']
            End_Date=bad_sensor_dates_dat.loc[xx, 'End_Date']
            Sensor=bad_sensor_dates_dat.loc[xx, 'Sensor']
            dat.loc[Start_Date:End_Date, Sensor]=np.nan
        #If sensor is mislabeled, switch label for indicated time period
        elif bad_sensor_dates_dat.loc[xx,'Action']=='switch_label':
            Start_Date=bad_sensor_dates_dat.loc[xx, 'Start_Date']
            End_Date=bad_sensor_dates_dat.loc[xx, 'End_Date']
            Sensor=bad_sensor_dates_dat.loc[xx, 'Sensor']
            Correct_Label=bad_sensor_dates_dat.loc[xx, 'Correct_Label']
            dat.loc[Start_Date:End_Date, Correct_Label]=dat.loc[Start_Date:End_Date, Sensor] #put data in correctly labeled column
            dat.loc[Start_Date:End_Date, Sensor]=np.nan #change the original location to NAN (no data was collected from this sensor)
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


#def precip_remove_drain_and_fill(precip_cumulative, obvious_error_precip_cutoff):
#    precip_edit=precip_cumulative.copy()
#    dPrecip=precip_edit -precip_edit.shift(1) #create incremental precip timeseries
#
#    #Set locations where sum of 3 sequential values > the precip refill error limit to 0 (some refills span several timesteps; generally under an hour however)
#    counter=0
#    for ii in range(2, len(dPrecip)):
#        if counter>0:
#            counter=counter-1
#            continue #skip iteration of loop if dPrecip already modified below
#    #If jump in initial precip series is over the cutoff
#        if abs(precip_edit[ii]-precip_edit[ii-2])>obvious_error_precip_cutoff:
#            print("PROBLEM!" + str(dPrecip.index.date[ii-2]))
#            #Find end of the filling event; when > 20 incremental values in a row are less than 2 cm
#            for xx in range(ii, ii+30):               
#                if (dPrecip[xx: xx+20]<(2)).all():
#                    dPrecip[ii-2:xx+1]=0
#                    print("Gage Drain/ Fill Event on " + str(dPrecip.index.date[ii-2]))
#                    print("found the end - removed at " + str(dPrecip.index[ii-2])+ ":" + "until" + str(dPrecip.index[xx]))
#                    break #continue to outer loop
#                else:
#                    print('continuing')
#                    counter=counter+1
#                    continue
#                    
#    new_cumulative= calculate_cumulative(cumulative_vals_orig=precip_edit, incremental_vals=dPrecip)
#    return(new_cumulative)

def precip_remove_drain_and_fill(precip_cumulative, obvious_error_precip_cutoff, n_cut):
    precip_edit=precip_cumulative.copy()
    dPrecip=precip_edit -precip_edit.shift(1) #create incremental precip timeseries
    
    #Set locations where sum of 3 sequential values > the precip refill error limit to 0 (some refills span several timesteps)
    counter=0
    for ii in range(1+n_cut, len(dPrecip)-n_cut):
        if counter>0:
            counter=counter-1
            continue
    #If sum of 3 values in a row have a value > cutoff, set all 3 to 0
        if abs(dPrecip[ii-1]+dPrecip[ii]+dPrecip[ii+1])>obvious_error_precip_cutoff:
            dPrecip[ii-n_cut:ii+n_cut+1]=0
            print("Gage Drain/ Fill Event on " + str(dPrecip.index.date[ii]))
            #print("    JUMP from " +str(precip_edit[ii-n_cut]) + " to " + str(precip_edit[ii+n_cut+1]))
            counter=n_cut

    new_cumulative= calculate_cumulative(cumulative_vals_orig=precip_edit, incremental_vals=dPrecip)
    return(new_cumulative)


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
    
def precip_remove_maintenance_noise(precip_cumulative, obvious_error_precip_cutoff, noise_cutoff):
    '''
    returns cumulative precip w/o fill and drain events
    '''
    precip_edit=precip_cumulative.copy()
    dPrecip=precip_edit -precip_edit.shift(1) #incremental precip
    dPrecip.loc[abs(dPrecip)>obvious_error_precip_cutoff]=0
    dPrecip.loc[(dPrecip>noise_cutoff) & (dPrecip.index.month>=8) & (dPrecip.index.month<=11)]=0 #set precip refills to 0 in fall months
    dPrecip.loc[abs(dPrecip)>noise_cutoff]=0 #set precip drains to 0
    
    #Re-sum cumulative timeseries
    new_cumulative=calculate_cumulative(precip_cumulative, dPrecip)
    return(new_cumulative)
    
def precip_remove_high_frequency_noiseNayak2010(precip_cumulative_og, noise, bucket_fill_drain_cutoff, n_forward_noise_free=20):
    '''
    precip_cumulative_og= pandas series of cumulative precipitation
    noise: numeric; limit for incremental change
    bucket_fill_drain_cutoff= numeric; limit for change that indicates a bucket refill or drain, performed during station maintenance
    '''
    precip_cumulative=precip_cumulative_og.copy()
    precip_cumulative=precip_cumulative.reindex() #reset index to integers from time
    precip_incremental=precip_cumulative-precip_cumulative.shift(1)
    flag='good' #create initial value for flag
    counter=0 #used to skip over iterations in outer loop which have already been edited by inner

    for ii in range(1, len(precip_incremental)):
        start_noise=np.nan
        end_noise=np.nan
        if flag=='skip_iteration': #this skips a single iteration if a single value has been edited
            #print('     skipping iteration' + str(precip_incremental.index[ii]))
            flag='good' #reset flag
            continue
        if counter>0: #this part skips as many iterations as have been edited below
            counter=counter-1
            #print("SKIPPING " + str(precip_incremental.index[ii]))
            continue
        if abs(precip_incremental[ii])>noise:
            start_noise=ii-1 #mark value before error
            #print("noise starts at "+ str(precip_incremental.index[ii])+ " ; " + str(ii))
            for jj in range(ii, len(precip_incremental)-n_forward_noise_free):
                #print(jj)
                newslice=precip_incremental[jj+1:jj+n_forward_noise_free+1] #slice of N values forward from location noise identified
                if (abs(newslice)>noise).any():
                    continue #additional noise is present in new slice; get new slice with subsequent loop iteration
                if(abs(newslice)<noise).all():
                  end_noise=jj+1 #jj is still a noisy value that should be replaced
                  if ii==jj:
                      #print("     single value removed at " + str(precip_incremental.index[jj]))
                      Dy=precip_cumulative[end_noise]-precip_cumulative[start_noise]
                      precip_incremental[jj]=Dy/2
                      precip_incremental[jj+1]=Dy/2#[jj:jj+2] selects 2 values (jj and jj+1) only
                      flag='skip_iteration' #need to skip next iteration of outer loop (altered precip[ii+1])
                      break #continue outer loop
                  if abs(precip_cumulative[end_noise]-precip_cumulative[start_noise])<bucket_fill_drain_cutoff:    #if issue is noise
                      precip_incremental[start_noise+1: end_noise]=np.nan #this does not change val @ end_noise
                      precip_cumulative[start_noise+1: end_noise]=np.nan
                      dY=precip_cumulative[end_noise] - precip_cumulative[start_noise]
                      dx=(end_noise)-(start_noise+1)+1
                      precip_incremental[start_noise+1: end_noise+1]=dY/dx #linear interpolation
                      #print("     interpolated noise at locations " + str(precip_incremental.index[start_noise+1]) + ":" +str(precip_incremental.index[end_noise]))
                      counter=len(precip_incremental[start_noise+1:end_noise+1])
                  if abs(precip_cumulative[end_noise]-precip_cumulative[start_noise])>bucket_fill_drain_cutoff: # if issue is gage maintenance
                      precip_incremental[start_noise+1:end_noise+1] =0 #no incremental precip occurs during bucket drain or refill
                      #print("     removed gage maintenance at  " + str(precip_incremental.index[start_noise+1]) + ":" +str(precip_incremental.index[end_noise]))
                  break #this simple exits the inner loop, continuing the outer
                  
            
    #print("recalculating cumulative")
    new_cumulative=calculate_cumulative(cumulative_vals_orig=precip_cumulative_og, incremental_vals=precip_incremental)
    new_cumulative.reindex_like(precip_cumulative_og) #reset index to time
    return(new_cumulative)
                    

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
    k: size of window (including the sample; 7 is equal to 3 on either side of value, which is the default in Matlab's implmentation)
    t0= number of standard deviations before replacing; default = 3
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
    vals[outlier_idx]=rolling_median
    return(vals)
    
def basic_median_outlier_strip(vals_orig, k, threshold, min_n_for_val=3):
    '''
    vals: pandas series of initial cumulative values
    k: window size
    threshold: cutoff threshold for values to strip
    
    RETURNS: series of instantaneous change values 
    '''
    vals=vals_orig.copy()
    rolling_median=vals.rolling(k, min_periods=min_n_for_val, center=True).median() #center=True keeps label on center value
    difference=np.abs(rolling_median-vals)
    outlier_idx=difference>threshold
    vals[outlier_idx]=rolling_median #set incremental change at index where cumulative is out of range to 0
    
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
 
    
    
    
    
    
def smooth_precip_Nayak2010(precip_cumulative):
    '''
    Routine for smoothing precipitation data from Nayak 2010 thesis/ 2008 paper.
    Returns dataframe with smoothed precip column (overwrites existing column)
      -relies on inner_precip_smoothing_func_Nayak2010, as included above in this module
    -----
    precip_cumulative: pandas series of data to smooth
    '''
    
    precip=precip_cumulative.copy() #copy, to avoid inadvertently altering original data
    precip_incr=precip-precip.shift(1)
    #precip_incr[0]=0
    #precip_incr[-1]=0
    #Smooth data in forward direction
    print("  smoothing data in forward direction; may take a minute")
    smooth_forward=inner_precip_smoothing_func_Nayak2010(precip_incr.values)
    #Smooth Data in backwards direction
    reverse_sorted_data=precip_incr.copy().sort_index(ascending=False).values
    print("  smoothing data in reverse direction; may take a minute")
    smooth_backwards=inner_precip_smoothing_func_Nayak2010(reverse_sorted_data)
    smooth_backwards=smooth_backwards[::-1] #sort forwards again, so in the correct order to store in dataframe

    #Average
    smooth_forward.index=precip_cumulative.index #Reindex in order to add back to original dataframe
    smooth_backwards.index=precip_cumulative.index #Reindex in order to add back to original dataframe
    
    dat2=pd.DataFrame()
    dat2['smooth_forward']=smooth_forward      #re-combine into single dataframe
    dat2['smooth_backwards']=smooth_backwards
    dat2['avg']=dat2[['smooth_forward', 'smooth_backwards']].mean(axis=1, skipna=False)
        
    #If first 3 values <0, set to 0. Same with end and last incremental 3 values.
    for ii in range(-3,0):
        if dat2.ix[ii, 'avg']<0:
            dat2.ix[ii, 'avg']=0
    for ii in range(0,3):
        if dat2.ix[ii, 'avg']<0:
            dat2.ix[ii, 'avg']=0   

    #New smooth precip data
    smooth_incr_precip=dat2['avg'] #overwrite old precip column with new smoothed values
    
    
    
    #Re-sum cumulative timeseries
    new_cumulative=calculate_cumulative(cumulative_vals_orig=precip_cumulative, incremental_vals=smooth_incr_precip)
    return(new_cumulative)
    
    
#def smooth_precip_Nayak2010_broken(precip_cumulative):
#    '''
#    Routine for smoothing precipitation data from Nayak 2010 thesis/ 2008 paper.
#    Returns dataframe with smoothed precip column (overwrites existing column)
#      -relies on inner_precip_smoothing_func_Nayak2010, as included above in this module
#    -----
#    precip_cumulative: pandas series of data to smooth
#    '''
#    
#    precip_copy=precip_cumulative.copy() #copy, to avoid inadvertently altering original data
#    precip_incr=precip_copy-precip_copy.shift(1)
#    #precip_incr[0]=0 #set first and last values to 0
#    #precip_incr[-1]=0
#    #Smooth data in forward direction
#    print("  smoothing data in forward direction; may take a minute")
#    smooth_forward=inner_precip_smoothing_func_Nayak2010(precip_incr.values)
#    #Smooth Data in backwards direction
#    reverse_sorted_data=precip_incr.copy().sort_index(ascending=False).values
#    print("  smoothing data in reverse direction; may take a minute")
#    smooth_backwards=inner_precip_smoothing_func_Nayak2010(reverse_sorted_data)
#    smooth_backwards=smooth_backwards[::-1] #sort forwards again, so in the correct order to store in dataframe
#
#    #Average
#    smooth_forward.index=precip_cumulative.index #Reindex in order to add back to original dataframe
#    smooth_backwards.index=precip_cumulative.index #Reindex in order to add back to original dataframe
#    
#    dat2=pd.DataFrame()
#    dat2['smooth_forward']=smooth_forward      #re-combine into single dataframe
#    dat2['smooth_backwards']=smooth_backwards
#    dat2['avg']=dat2[['smooth_forward', 'smooth_backwards']].mean(axis=1)
#    
#    #If first 3 values <0, set to 0. Same with end and last incremental 3 values.
#    for ii in range(-3,0):
#        if dat2.ix[ii, 'avg']<0:
#            dat2.ix[ii, 'avg']=0
#    for ii in range(0,3):
#        if dat2.ix[ii, 'avg']<0:
#            dat2.ix[ii, 'avg']=0   
#    
#    #New smooth precip data
#    #smooth_incr_precip=dat2['avg'] #overwrite old precip column with new smoothed values
#    
#    #Re-sum cumulative timeseries
#    #new_cumulative=calculate_cumulative(cumulative_vals_orig=precip_cumulative, incremental_vals=smooth_incr_precip)
#    
#    return(smooth_backwards)
    
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

def calculate_cumulative(cumulative_vals_orig, incremental_vals):
    '''
    function to calculate cumulative timeseries from two things: an input (edited) incremental series, and the original cumulative series.

    '''
    #Original values in cumulative series
    cumulative_vals_old=cumulative_vals_orig.copy()
        
    #Calculate cumulative sum of incremental values
    new_cumulative=incremental_vals.cumsum()
    
    #Adjust so begins as same absolute value as input
    if not np.isnan(cumulative_vals_old[0]):
        if cumulative_vals_orig.isnull().any():
            print("STOP! Series contains NANs, which will result in unintended jumps in cumulative timeseries!")
            print("NANs at " +str(cumulative_vals_old.index[cumulative_vals_old.isnull()]))
        start_value=cumulative_vals_old[0]
        new_cumulative = new_cumulative + start_value
        new_cumulative[0]=cumulative_vals_old[0] #needed, as first value of incremental series is a NAN
        
    #If data begins with NANs, must adjust based on first valid value, not first value
    else:
        start_data_index=cumulative_vals_old.first_valid_index()
        start_value=cumulative_vals_old[start_data_index]
        new_cumulative=new_cumulative+start_value
    return(new_cumulative)
    
def plot_comparrison(df_old, df_new, data_col_name, label_old='original', label_new='new'):
    ax=df_old[data_col_name].plot(label=label_old, title=df_old[data_col_name].name, color='red')
    df_new[data_col_name].plot(color='blue', ax=ax, label=label_new)
    plt.legend()


def vector_average_wind_direction(WS, WD):
    '''
    Calculate vector-average wind direction from wind direction (0-360) and wind speed.
    WS -  wind speed in m/s
    WD - vector of  wind direction in degrees (0-360)
    
    Should only be used if instrument not already recording vector-average wind direction
    
    Output is a single number - vector averagae wind direction during the period of input data
    ''' 
    #Calculate Vector Mean Wind Direction
    WS=WS.astype(np.float64)
    WD=WD.astype(np.float64)
    V_east = np.mean(WS * np.sin(WD * (np.pi/180)))
    V_north = np.mean(WS * np.cos(WD * (np.pi/180)))
    mean_WD = np.arctan2(V_east, V_north) * (180/np.pi)
    #Translate output range from -180 to +180 to 0-360.
    if mean_WD<0:
        mean_WD=mean_WD+360       
    return(mean_WD)

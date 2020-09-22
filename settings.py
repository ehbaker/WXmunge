'''
Location to store glacier name and station, so accessible to multiple other scripts. 

Also stores base path for server (to keep from angering the folks)
'''
import pandas as pd

#Set desired output date format
out_date_format='%Y/%m/%d %H:%M'

#base_path=r"Q:/Project Data/GlacierData/Benchmark_Program/"
base_path=r"C:\Users\ehbaker\Documents/BrokenServer/"

Glacier='Gulkana'
Station='1480'

def get_settings(Glacier, Station):
   
    
    #Set timezone
    if Glacier in ['Gulkana', 'Wolverine', 'LemonCreek', 'JuneauIcefield']:
        timezone='America/Anchorage'
    if Glacier in ['Sperry']:
        timezone='America/Denver'
    if Glacier in ['SouthCascade']:
        timezone='US/Pacific'
    
    #Settings for main Wolverine and Gulkana Sites
    if (Glacier +Station=='Wolverine990') | (Glacier +Station =='Gulkana1480'):
    
        #precip columns
        precip_columns=['TPGCumulative', 'StageCumulative']
    
        #temp columns
        temp_columns=['Tpassive1', 'Tpassive2', 'TAspirated1', 'TAspirated2']
        
        #wind columns
        wind_col='WindSpeed'
        wind_dir_columns=['WindDir', 'VecAvgWindDir']
        
        #best temperature sensor
        primary_temp_column='TAspirated1'
        
        #Indicate if there is a precip gage change and need for bias-adjustment
        precip_gage_change=True
        
        general_data_columns=['RelHum', 'WindSpeed', 'WindGustSpeed']
        wind_dir_columns=['WindDir', 'VecAvgWindDir']
        if Glacier + Station =='Wolverine990':
            general_data_columns=['RelHum', 'WindSpeed', 'WindGustSpeed', 'Barom']
    
    if Glacier +Station=='Gulkana1725':
        precip_columns=['TPGCumulative']
        temp_columns=['Tpassive1', 'Tpassive2', 'Tpassive3']
        wind_col='WindSpeed'
        wind_dir_columns=['VecAvgWindDir']
        primary_temp_column='Tpassive1'
        precip_gage_change=False
        general_data_columns=['WindSpeed', 'RadiationIn', 'RadiationOut'] #Removed snow depth b/c it's all crap
    
    if Glacier == 'JuneauIcefield':
#        out_columns=['UTC_time', 'local_time', 'Tpassive1']
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=[]
        
#        out_columns=temp_columns
        primary_temp_column='Tpassive1'
        wind_dir_columns=[]
        
        #Indicate if there is a precip gage change and need for bias-adjustment
        precip_gage_change=False
        
    if (Glacier + Station=='Sperry1920') | (Glacier + Station=='SouthCascade270'): #this is the flathead snotel site
        precip_columns=['Precipitation']
        temp_columns=['Temperature']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=[]
        primary_temp_column='Temperature'
        
        #Indicate if there is a precip gage change and need for bias-adjustment
        precip_gage_change=False
        
    if (Glacier + Station=='Sperry2440'): #this is the flathead snotel site
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col='WindSpeed'
        wind_dir_columns=['WindDir']
        general_data_columns=['WindSpeed', 'WindGustSpeed', 'RelHum', 'SW_in','SW_out','LW_in','LW_out']
        primary_temp_column='Tpassive1'
        
        #Indicate if there is a precip gage change and need for bias-adjustment
        precip_gage_change=False
        
    if (Glacier + Station== 'Wolverine1420') | (Glacier + Station== 'Gulkana1920'): #If a JWS station; campbell loggers @ high elevation
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col='WindSpeed'
        wind_dir_columns=['VecAvgWindDir']
        general_data_columns=['RadiationIn', 'RadiationOut', 'WindSpeed']
        if Glacier+Station=='Wolverine1420':
            general_data_columns=general_data_columns+ ['Barom']
        primary_temp_column='Tpassive1'
        precip_columns=[]
        if Glacier + Station =='Wolverine1420':
            precip_columns=['TPGCumulative']
        precip_gage_change=False    
        
    if Glacier + Station == 'LemonCreek5':
        precip_columns=['Precipitation']
        temp_columns=['Temperature']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=[]
        primary_temp_column='Temperature'  
    
        precip_gage_change=False    
        
    if Glacier +Station=='Wolverine370':
        precip_columns=['TipCumulative', 'TPGCumulative']
        temp_columns=['Tpassive1']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=['Discharge']
        primary_temp_column='Tpassive1' 
        
        precip_gage_change=True
        
    if Glacier + Station == 'SouthCascade1640':
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=[]
        primary_temp_column='Tpassive1'  
    
        precip_gage_change=False
        
        
    if Glacier + Station == 'JuneauIcefieldCamp18AWS':
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col='WindSpeed'
        wind_dir_columns=['VecAvgWindDir']
        general_data_columns=['Barom', 'RelHum', 'WindGustSpeed', 'WindSpeed']
        primary_temp_column='Tpassive1'  
        
    if Glacier + Station in ['JuneauIcefieldCamp17AWS', 'LemonCreekCamp17AWS']: #these are the same site; 2 names
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col='WindSpeed'
        wind_dir_columns=['VecAvgWindDir', 'WindDir']
        general_data_columns=['Barom', 'RelHum', 'WindGustSpeed', 'WindSpeed']
        primary_temp_column='Tpassive1'  
        precip_gage_change=False    
            
    if Glacier + Station in ['JuneauIcefieldCamp10AWS', 'LemonCreekCamp10AWS']:
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col='WindSpeed'
        wind_dir_columns=['WindDir']
        general_data_columns=['Barom', 'RelHum', 'WindGustSpeed', 'WindSpeed', 'RadiationIn']
        primary_temp_column='Tpassive1'
        precip_gage_change=False
        
    if Glacier + Station == 'SouthCascade1830':
        precip_columns=[] #the data that is in there is worthless in "TipBucketCumulative'
        temp_columns=['Tpassive1', 'Tpassive2']
        wind_col='WindSpeed'
        wind_dir_columns=['WindDir']
        general_data_columns=['RelHum', 'WindSpeed', 'RadiationIn']
        primary_temp_column='Tpassive1'
        precip_gage_change=False
        
    if Glacier + Station == 'SouthCascade1640':
        precip_columns=[]
        temp_columns=['Tpassive1']
        wind_col=''
        wind_dir_columns=[]
        general_data_columns=[]
        primary_temp_column='Tpassive1'
        precip_gage_change=False
        
    
    
    
    #Make a list of ALL data columns    
    data_columns= temp_columns +precip_columns +[wind_col] +wind_dir_columns+general_data_columns
    data_columns=list(filter(None, data_columns)) #drop any empty labels
    data_columns=list(pd.Series(data_columns).drop_duplicates())
    
    return(data_columns, general_data_columns, out_date_format, precip_columns, precip_gage_change, primary_temp_column, temp_columns, timezone, wind_col, wind_dir_columns)


#def get_level_0_only_columns(Glacier, Station):
#    #Settings for main Wolverine and Gulkana Sites
#    if (Glacier +Station=='Wolverine990'):
#        level_0_only_columns=[]
#    if (Glacier +Station =='Gulkana1480'):
#        level_0_only_columns=['RadiationIn', 'RadiationOut', 'SnowDepth']
#    
#    
#    if Glacier +Station=='Gulkana1725':
#        level_0_only_columns=['Tpassive2']
        

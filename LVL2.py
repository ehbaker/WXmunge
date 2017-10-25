'''
  LVL2 WX Cleaning Functions
'''
import numpy as np
    
def vector_average_wind_direction(WS, WD):
    '''
    Calculate vector-average wind direction from wind direction (0-360) and wind speed.
    WS -  wind speed in m/s
    WD - vector of  wind direction in degrees (0-360)
    
    Should only be used if instrument not already recording vector-average wind direction
    ''' 
    #Calculate Vector Mean Wind Direction
    WS=WS.astype(np.float64)
    WD=WD.astype(np.float64)
    V_east = np.mean(WS) * np.mean(np.sin(WD * (np.pi/180)))
    V_north = np.mean(WS) * np.mean(np.cos(WD * (np.pi/180)))
    mean_WD = np.arctan2(V_east, V_north) * (180/np.pi)
    #Translate output range from -180 to +180 to 0-360.
    if mean_WD<0:
        mean_WD=mean_WD+180       
    return(mean_WD)
    

    

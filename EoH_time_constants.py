# -*- coding: utf-8 -*-
"""
Created on Sat Nov 25 16:11:47 2023

@author: Claire Halloran, University of Oxford

Calculates thermal time constants of homes in the Electrification of Heat trial
based on an exponential fit of indoor temperature drop.

"""

import pandas as pd
import numpy as np
import glob
import scipy as sp

def break_into_intervals(df):
    # Calculate time difference
    time_diff = df.index.to_series().diff().dt.total_seconds().fillna(0)
    mask = time_diff > 120  # Two minutes in seconds

    # Grouping based on intervals
    groups = mask.cumsum()
    intervals = df.groupby(groups)

    # Creating separate DataFrames for each interval
    dfs = [interval for _, interval in intervals if len(interval)>=duration\
           and interval['Internal_Air_Temperature'].isna().sum()==0\
               and interval['External_Air_Temperature'].isna().sum()==0\
                   # mean temperature difference of 5 C between indoor and outdoor temperature
                    and interval['Internal_Air_Temperature'].mean()-interval['External_Air_Temperature'].mean()>5\
                        # require an overall change in indoor air temperature
                        and interval['Internal_Air_Temperature'].diff().sum()!=0.\
                            # ensure that external temperature doesn't vary more than 2 C
                            and (interval['External_Air_Temperature'].max()-interval['External_Air_Temperature'].min())<=2. 
                            ]
    
    return dfs

def exponential_decay(t, A, tau, C):
     return A * np.exp(-t/tau) + C
 
 # Fit exponential decay to each DataFrame
def fit_exponential_decay(df, C):
     t = (df.index-df.index.min()).to_series().dt.total_seconds().values
     y = df['Internal_Air_Temperature'].values - C
     y = np.log(y)
     K, A_log = np.polyfit(t, y, 1)
     A = np.exp(A_log)
     tau = -1/K
     return A, tau
def fit_exp_nonlinear(df):
     t = (df.index-df.index.min()).to_series().dt.total_seconds().values
     y = df['Internal_Air_Temperature'].values

     opt_parms, parm_cov = sp.optimize.curve_fit(exponential_decay, t, y, maxfev=1000)
     A, tau, C = opt_parms
     return A, tau, C


# find all samples
dataset_1 = glob.glob('Data/Electrification of Heat/Dataset 1/*.csv')
dataset_2 = glob.glob('Data/Electrification of Heat/Dataset 2/*.csv')
all_files = dataset_1 + dataset_2
duration_list = [30,60,90,120,180,240]

tau_df = pd.DataFrame(np.nan, index=np.array(all_files), columns=np.array(duration_list))
tau_df.index = tau_df.index.str.removeprefix('Data/Electrification of Heat/Dataset 1\Property_ID=').str.removesuffix('.csv')
tau_df.index = tau_df.index.str.removeprefix('Data/Electrification of Heat/Dataset 2\Property_ID=').str.removesuffix('.csv')

for duration in duration_list:
    house_tau_list = []
    house_tau_variation_list = []
    # import sample data
    for file in all_files:
        EOH_house = pd.read_csv(file, parse_dates=['Timestamp'],index_col='Timestamp')
        print('Reading '+file)
        
        #%% identifying time periods when heat pump is off and temperature is decreasing
        if 'Heat_Pump_Energy_Output' not in EOH_house.columns:
            house_tau_list.append(np.nan)
            house_tau_variation_list.append(np.nan)
            continue
        # filter to exclude summer months
        heating_season = pd.concat([EOH_house['11-2020':'04-2021'],EOH_house['10-2021':'04-2022']])
        heat_pump_installed = heating_season[~heating_season['Heat_Pump_Energy_Output'].isna()]
        
        #%% heat pump energy output not increasing (heat pump off)
        heat_off = heat_pump_installed[(heat_pump_installed['Heat_Pump_Energy_Output'].diff()==0.)&(heat_pump_installed['Heat_Pump_Heating_Flow_Temperature'].diff()<=0.)]
    
        # check if boiler or backup heater is on if installed
        if 'Boiler_Energy_Output' in heat_off.columns:
            heat_off = heat_off[heat_off['Boiler_Energy_Output'].diff()==0.]
        
        if 'Back-up_Heater_Energy_Consumed' in heat_off.columns:
            heat_off = heat_off[heat_off['Back-up_Heater_Energy_Consumed'].diff()==0.]
        
        if 'Immersion_Heater_Energy_Consumed' in heat_off.columns:
            heat_off = heat_off[heat_off['Immersion_Heater_Energy_Consumed'].diff()==0.]
            
        # colder outside than inside-- only get winter!!!
        colder_outside = heat_off[heat_off['External_Air_Temperature']<heat_off['Internal_Air_Temperature']]
        # ensure outside of house is below 15.5 C
        colder_outside = colder_outside[colder_outside['External_Air_Temperature']<15.5]
        # when temperature is decreasing
        decreasing_temperature = colder_outside[colder_outside['Internal_Air_Temperature'].diff()<=0.]
        # exclude rapid decreases in temperature -- assume door/window was opened
        decreasing_temperature = decreasing_temperature[decreasing_temperature['Internal_Air_Temperature'].diff()>-5.]

        #%% section off consecutive time periods     
        separate_dataframes = break_into_intervals(decreasing_temperature)
        
        #%% fit exponential decay
        tau_list = []
        A_list = []
        C_list = []
        for df_interval in separate_dataframes:
            
            C = df_interval['External_Air_Temperature'].mean()
            C_list.append(C)
            A, tau = fit_exponential_decay(df_interval, C)
                        
            tau_list.append(tau/3600) # convert tau to hours
            A_list.append(A)
            x_fit = np.linspace(0, (df_interval.index - df_interval.index.min()).to_series().dt.total_seconds().max(), 100)
            y_fit = exponential_decay(x_fit, A, tau, C)
            
        tau_series = pd.Series(tau_list)
        tau_series = tau_series.mask(tau_series.sub(tau_series.mean()).div(tau_series.std()).abs().gt(3))
        house_tau_list.append(tau_series.mean())
        house_tau_variation_list.append(tau_series.std())
        
    tau_df[duration] = house_tau_list

tau_df.to_csv('Resources/EoH time constants.csv')
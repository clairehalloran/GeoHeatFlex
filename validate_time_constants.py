# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 16:35:45 2023

@author: Claire Halloran, University of Oxford

Validates gas-based thermal time constants of LSOAs and DZs based on 
Electrification of Heat trial data and Canet and Quadrdan 2023 results.

"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#%% read files
EOH_time_constants = pd.read_csv('Resources/EoH time constants.csv', index_col='Unnamed: 0')

LSOAs = gpd.read_file('Resources/LSOA_gas_time_constants.geojson')
DZs= gpd.read_file('Resources/DZ_gas_time_constants.geojson')
DZs.set_index('index', inplace=True)
LSOAs.set_index('index', inplace=True)

canet = pd.read_csv('Data/UKERC/01 - Thermal_Characteristics/Thermal_characteristics_beforeEE.csv')
canet_retrofit = pd.read_csv('Data/UKERC/01 - Thermal_Characteristics/Thermal_characteristics_afterEE.csv')

#%% comparison with Canet and Qadrdan 2023 results based on bottom-up EPC method

# pull out only comparable data-- gas heated homes with medium thermal capacity
canet_gas = canet[(canet['Heating systems']=='gas boiler')& (canet['Thermal capacity level']=='medium')]

LSOAs['Canet average thermal capacity'] = pd.Series(np.nan, LSOAs.index)
LSOAs['Canet average thermal losses'] = pd.Series(np.nan, LSOAs.index)
LSOAs['Canet average floor area'] = pd.Series(np.nan, LSOAs.index)

for LSOA in LSOAs.index:
    canet_gas_LSOA = canet_gas[canet_gas['LSOA_code']==LSOA]
    total_households = canet_gas_LSOA['Number of dwellings'].sum()
    canet_thermal_capacity = (canet_gas_LSOA['Number of dwellings']*canet_gas_LSOA['Average thermal capacity kJ/K']).sum()/total_households
    canet_thermal_losses = (canet_gas_LSOA['Number of dwellings']*canet_gas_LSOA['Average thermal losses kW/K']).sum()/total_households
    canet_floor_area = (canet_gas_LSOA['Number of dwellings']*canet_gas_LSOA['Average floor area m2']).sum()/total_households
    
    LSOAs.at[LSOA,'Canet average thermal capacity'] = canet_thermal_capacity
    LSOAs.at[LSOA,'Canet average thermal losses'] = canet_thermal_losses
    LSOAs.at[LSOA,'Canet average floor area'] = canet_floor_area

#%% compare thermal losses with retrofit
canet_retrofit_gas = canet_retrofit[(canet_retrofit['Heating systems']=='gas boiler')& (canet_retrofit['Thermal capacity level']=='medium')]

LSOAs['Canet retrofit average thermal losses'] = pd.Series(np.nan, LSOAs.index)

for LSOA in LSOAs.index:
    canet_gas_LSOA = canet_retrofit_gas[canet_retrofit_gas['LSOA_code']==LSOA]
    total_households = canet_gas_LSOA['Number of dwellings'].sum()
    canet_thermal_losses = (canet_gas_LSOA['Number of dwellings']*canet_gas_LSOA['Average thermal losses kW/K']).sum()/total_households
    
    LSOAs.at[LSOA,'Canet retrofit average thermal losses'] = canet_thermal_losses

#%% compare all time constants KDE

canet_medium = canet[canet['Thermal capacity level']=='medium']
canet_retrofit_medium = canet_retrofit[canet_retrofit['Thermal capacity level']=='medium']

fig, ax = plt.subplots()

pd.concat([LSOAs['Thermal time constant [h]'],DZs['Thermal time constant [h]']]).plot.kde(
    ax = ax, label = 'Heating consumption-based (this paper)', grid = False)
(canet_medium['Average thermal capacity kJ/K']/3.6e3/\
 canet_medium['Average thermal losses kW/K']).plot.kde(
    ax = ax, label = 'EPC-based (current)', grid = False)
(canet_retrofit_medium['Average thermal capacity kJ/K']/3.6e3/\
 canet_retrofit_medium['Average thermal losses kW/K']).plot.kde(
    ax = ax, label = 'EPC-based (retrofit)', grid = False)
EOH_time_constants['90'].plot.kde(
    ax = ax, color='C4', label = 'Indoor temperature-based', grid = False)

ax.set_xlabel('Time constant [h]')
ax.set_ylabel('Sample density')
ax.legend()

ax.set_xlim(0,150)
ax.grid()
plt.savefig('Plots/KDE time constant comparison.jpg', dpi = 300)

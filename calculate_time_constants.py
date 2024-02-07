# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 22:50:28 2023

@author: Claire Halloran, University of Oxford

Calculates thermal time constants based on heating losses and estimated thermal 
capacity in each region. Thermal capacity is estimated based on the mean number
of rooms in dwellings in each region, and total thermal energy storage capacity
is calculated from thermal capacity for a given temperature window.

"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

#%% estimate thermal capacity based on number of rooms

LSOA_rooms = pd.read_csv('Data/England_and_Wales_census_2011_number_of_rooms.csv',
                         index_col='geography code')

# clean up column names
LSOA_rooms.columns = LSOA_rooms.columns.str.removeprefix('Rooms: ').str.removesuffix('; measures: Value')

DZ_rooms = pd.read_excel('Data/Scotland_census_2011_number_of_rooms.xlsx',
                         header = 11,
                         index_col = 'Unnamed: 1')
DZ_rooms.drop('Datazone 2011', inplace= True)

#%% calculate mean number of rooms per household in each region

LSOA_rooms['Mean rooms'] = (LSOA_rooms['1 room']\
                            +LSOA_rooms['2 rooms']*2\
                                +LSOA_rooms['3 rooms']*3\
                                    +LSOA_rooms['4 rooms']*4\
                                        +LSOA_rooms['5 rooms']*5\
                                            +LSOA_rooms['6 rooms']*6\
                                                       +LSOA_rooms['7 rooms']*7\
                                                           +LSOA_rooms['8 rooms']*8\
                                                               +LSOA_rooms['9 or more rooms']*9)/\
    LSOA_rooms['All categories: Number of rooms']
    
DZ_rooms['Mean rooms'] = (DZ_rooms['One room']\
                            +DZ_rooms['Two rooms']*2\
                                +DZ_rooms['Three rooms']*3\
                                    +DZ_rooms['Four rooms']*4\
                                        +DZ_rooms['Five rooms']*5\
                                            +DZ_rooms['Six rooms']*6\
                                                       +DZ_rooms['Seven rooms']*7\
                                                           +DZ_rooms['Eight rooms']*8\
                                                               +DZ_rooms['Nine or more rooms']*9)/\
    DZ_rooms['All occupied household spaces']

#%% load and join heating loss data

LSOAs = gpd.read_file('Resources/LSOA_gas_heat_loss_2017-2021.geojson',driver='GeoJSON')
DZs = gpd.read_file('Resources/DZ_gas_heat_loss_2017-2021.geojson',driver='GeoJSON')
DZs.set_index('index', inplace=True)
LSOAs.set_index('index', inplace=True)

LSOAs = LSOAs.join(LSOA_rooms['Mean rooms'], how = 'inner')
DZs = DZs.join(DZ_rooms['Mean rooms'], how = 'inner')

#%% plot of mean rooms
vmin = min(LSOAs['Mean rooms'].min(),
           DZs['Mean rooms'].min())
vmax=max(LSOAs['Mean rooms'].max(),
         DZs['Mean rooms'].max())
fig, ax = plt.subplots()
DZs.plot(column = 'Mean rooms',
         ax = ax,
         cmap = 'viridis',
         vmin=vmin,
         vmax=vmax,
         missing_kwds={'color': 'lightgrey'})
LSOAs.plot(column ='Mean rooms',
           ax = ax,
           legend = True,
           legend_kwds = {'label':'Rooms'},
           cmap = 'viridis',
           vmin=vmin,
           vmax=vmax,
           missing_kwds={'color': 'lightgrey'})
plt.title('Mean rooms per dwelling')
plt.axis("off")
plt.savefig('Rooms per household.jpg', dpi=1000)

#%% make an assumption about average floor area per room

floor_area_per_room = 17.6

LSOAs['Estimated floor area [m2]'] = floor_area_per_room*LSOAs['Mean rooms']
DZs['Estimated floor area [m2]'] = floor_area_per_room*DZs['Mean rooms']

# SAP 2012 medium
specific_thermal_capacity = 250/3600 # kWh/m2/C

LSOAs['Thermal capacity [kWh/C]']= specific_thermal_capacity * LSOAs['Estimated floor area [m2]']
DZs['Thermal capacity [kWh/C]']= specific_thermal_capacity * DZs['Estimated floor area [m2]']

#%% plot thermal capacity distribution

fig, ax = plt.subplots()

(pd.concat([LSOAs['Thermal capacity [kWh/C]'],DZs['Thermal capacity [kWh/C]']])*3.6).plot.hist(bins= 50, ax = ax, xlim = [10,35])

ax.set_xlabel('Thermal capacity [MJ/C]')
ax.set_ylabel('Count of regions')

#%% map thermal capacity
degree_sign = u'\N{DEGREE SIGN}'

vmin = min(LSOAs['Thermal capacity [kWh/C]'].quantile(0.01),
           DZs['Thermal capacity [kWh/C]'].quantile(0.01))
vmax=max(LSOAs['Thermal capacity [kWh/C]'].quantile(0.99),
         DZs['Thermal capacity [kWh/C]'].quantile(0.99))
fig, ax = plt.subplots()
DZs.plot(column = 'Thermal capacity [kWh/C]',
         ax = ax,
         cmap = 'viridis',
         vmin=vmin,
         vmax=vmax,
         missing_kwds={'color': 'grey'})
LSOAs.plot(column ='Thermal capacity [kWh/C]',
           ax = ax,
           legend = True,
           legend_kwds = {'label':'kWh/'+degree_sign+'C'},
           cmap = 'viridis',
           vmin=vmin,
           vmax=vmax,
           missing_kwds={'color': 'grey'})
# plt.title('Mean thermal time constant')
plt.axis("off")
plt.savefig('Plots/thermal capacity.jpg', dpi=1000)


#%% calculate thermal time constants

LSOAs['Thermal time constant [h]']=LSOAs['Thermal capacity [kWh/C]']/\
    LSOAs['Mean gas heating losses 2017-2021 (kW/C)']
DZs['Thermal time constant [h]']=DZs['Thermal capacity [kWh/C]']/\
    DZs['Mean gas heating losses 2017-2021 (kW/C)']
    
#%% plot of thermal time constants
vmin = min(LSOAs['Thermal time constant [h]'].quantile(0.01),
           DZs['Thermal time constant [h]'].quantile(0.01))
vmax=max(LSOAs['Thermal time constant [h]'].quantile(0.99),
         DZs['Thermal time constant [h]'].quantile(0.99))
fig, ax = plt.subplots()
DZs.plot(column = 'Thermal time constant [h]',
         ax = ax,
         cmap = 'PuOr_r',
         vmin=vmin,
         vmax=vmax,
         missing_kwds={'color': 'grey'})
LSOAs.plot(column ='Thermal time constant [h]',
           ax = ax,
           legend = True,
           legend_kwds = {'label':'Thermal time constant [h]'},
           cmap = 'PuOr_r',
           vmin=vmin,
           vmax=vmax,
           missing_kwds={'color': 'grey'})
# plt.title('Mean thermal time constant')
plt.axis("off")
plt.savefig('Plots/Thermal time constant.jpg', dpi=1000)

#%% save results

LSOAs.to_file('Resources/LSOA_gas_time_constants.geojson',driver='GeoJSON')
DZs.to_file('Resources/DZ_gas_time_constants.geojson',driver='GeoJSON')

#%% create a simple, merged version for use as power system planning input
# need to include time constant and total number of households

# join number of occupied households from 2011 census
LSOAs = LSOAs.join(LSOA_rooms['All categories: Number of rooms'], how = 'inner')
DZs = DZs.join(DZ_rooms['All occupied household spaces'], how = 'inner')
# rename columns to occupied households
LSOAs = LSOAs.rename(columns={'All categories: Number of rooms':'Households'})
DZs = DZs.rename(columns={'All occupied household spaces':'Households'})

time_constants = pd.concat([LSOAs[['Thermal time constant [h]','Thermal capacity [kWh/C]','Households','geometry']], 
                            DZs[['Thermal time constant [h]','Thermal capacity [kWh/C]','Households','geometry']]])

time_constants.to_file('Results/regional_thermal_time_constants.geojson',driver='GeoJSON')

#%% calculate the total thermal energy that can be stored for a given temperature window

delta_T = 3 # celsius

LSOAs['Total thermal energy storage [kWh]'] = delta_T*LSOAs['Thermal capacity [kWh/C]']*LSOAs['Households']
DZs['Total thermal energy storage [kWh]'] = delta_T*DZs['Thermal capacity [kWh/C]']*DZs['Households']

national_TES_capacity = (LSOAs['Total thermal energy storage [kWh]'].sum() +\
    DZs['Total thermal energy storage [kWh]'].sum())/1e6 #kWh to GWh
    
print('Total thermal energy storage capacity: '+national_TES_capacity+' GWh(th)')
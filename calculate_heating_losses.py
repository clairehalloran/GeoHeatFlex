# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 19:40:02 2023

@author: Claire Halloran, University of Oxford

Calculates residential heating losses based on HDDs and historical gas demand.

"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

#%% import regions with HDDs calculated

LSOAs = gpd.read_file('Resources/LSOA_HDDs_2010-2022.geojson',
                      index_col = 'LSOA11CD')
DZs = gpd.read_file('Resources/DZ_HDDs_2010-2022.geojson',
                    index_col = 'DataZone')
DZs.set_index('DataZone', inplace=True)
LSOAs.set_index('LSOA11CD', inplace=True)
#%% import annual heating demand
gas_demand = pd.read_excel('Data/LSOA_domestic_gas_2010-21.xlsx', 
                           sheet_name = ['2017','2018','2019','2020','2021'],
                           header=4,
                           index_col='LSOA code')
#%% import Energy Consumption in the UK consumption by fuel and end use

ECUK = pd.read_excel('Data/ECUK_2022_End_Use_tables_27102022.xlsx',sheet_name='Table U2', header = 4)

#%% attach annual heating demand to each region

# maybe add a for loop to do this for each year, and save the heating loss constant?
gas_years = [2017,2018,2019,2020,2021]

for year in gas_years:
    gas_demand[f'{year}'].columns = gas_demand[f'{year}'].columns.str.replace('\n', ' ')
    gas_demand[f'{year}'] = gas_demand[f'{year}'].add_suffix(' gas demand')
    gas_demand[f'{year}'] = gas_demand[f'{year}'].add_prefix(f'{year} ')

    # join gas demand and LSOAs/DZs
    DZs = DZs.join(gas_demand[f'{year}'][f'{year} Mean  consumption (kWh per meter) gas demand'], how='inner')
    LSOAs = LSOAs.join(gas_demand[f'{year}'][f'{year} Mean  consumption (kWh per meter) gas demand'], how='inner')
    
    # scale gas demand by share of domestic natural gas used for space heating
    space_heating_share = ECUK[(ECUK['Sector']=='Domestic')&(ECUK['Year']==year)&(ECUK['End use']== 'Space heating')]['Natural gas'].to_numpy()/\
        ECUK[(ECUK['Sector']=='Domestic')&(ECUK['Year']==year)&(ECUK['End use']== 'Overall total')]['Natural gas'].to_numpy()
    
    DZs[f'{year} Mean space heating gas demand (kWh per meter)'] = DZs[f'{year} Mean  consumption (kWh per meter) gas demand']*space_heating_share
    LSOAs[f'{year} Mean space heating gas demand (kWh per meter)'] = LSOAs[f'{year} Mean  consumption (kWh per meter) gas demand']*space_heating_share
    
    # plot mean space heating gas consumption per gas meter
    vmin = min(LSOAs[f'{year} Mean space heating gas demand (kWh per meter)'].quantile(0.005),
               DZs[f'{year} Mean space heating gas demand (kWh per meter)'].quantile(0.005))
    vmax=max(LSOAs[f'{year} Mean space heating gas demand (kWh per meter)'].quantile(0.995),
             DZs[f'{year} Mean space heating gas demand (kWh per meter)'].quantile(0.995))
    fig, ax = plt.subplots()
    DZs.plot(column = f'{year} Mean space heating gas demand (kWh per meter)',
             ax = ax,
             cmap = 'magma',
             vmin=vmin,
             vmax=vmax,
             missing_kwds={'color': 'lightgrey'})
    LSOAs.plot(column = f'{year} Mean space heating gas demand (kWh per meter)',
               ax = ax,
               legend = True,
               legend_kwds = {'label':'kWh per meter'},
               cmap = 'magma',
               vmin=vmin,
               vmax=vmax,
               missing_kwds={'color': 'lightgrey'})
    plt.title(f'Mean household gas demand {year}')
    plt.axis("off")
    plt.savefig(f'Plots/Gas space heating demand {year}.jpg', dpi=300)

#%% calculate heating losses based on heating demand and HDDs
# note that years don't align for annual gas and electricity demand-- calculate separately

# since gas data at LSOA level is weather-corrected, sum HDDs and gas demand
# sum propegates NaNs-- some areas only have gas consumption for a few years
DZs['Mean household gas space heating demand 2017-2021'] = sum(DZs[f'{year} Mean space heating gas demand (kWh per meter)'] for year in gas_years)
LSOAs['Mean household gas space heating demand 2017-2021'] = sum(LSOAs[f'{year} Mean space heating gas demand (kWh per meter)'] for year in gas_years)

DZs['Total gas HDDs 2017-2021'] = sum(DZs[f'{year} gas HDDs'] for year in gas_years)
LSOAs['Total gas HDDs 2017-2021'] = sum(LSOAs[f'{year} gas HDDs'] for year in gas_years)
 
# from 2017 onward to get long-run average heating losses
DZs['Mean gas heating losses 2017-2021 (kW/C)'] = DZs['Mean household gas space heating demand 2017-2021']/\
    (DZs['Total gas HDDs 2017-2021']*24) # convert to heating degree hours to get kW
LSOAs['Mean gas heating losses 2017-2021 (kW/C)'] = LSOAs['Mean household gas space heating demand 2017-2021']/\
    (LSOAs['Total gas HDDs 2017-2021']*24) # convert to heating degree hours to get kW
    

#%% plot mean gas heating losses
degree_sign = u'\N{DEGREE SIGN}'

vmin = min(LSOAs['Mean gas heating losses 2017-2021 (kW/C)'].quantile(0.005),
           DZs['Mean gas heating losses 2017-2021 (kW/C)'].quantile(0.005))
vmax=max(LSOAs['Mean gas heating losses 2017-2021 (kW/C)'].quantile(0.995),
         DZs['Mean gas heating losses 2017-2021 (kW/C)'].quantile(0.995))
fig, ax = plt.subplots()
DZs.plot(column = 'Mean gas heating losses 2017-2021 (kW/C)',
         ax = ax,
         cmap = 'inferno_r',
         vmin=vmin,
         vmax=vmax,
         missing_kwds={'color': 'lightgrey'})
LSOAs.plot(column ='Mean gas heating losses 2017-2021 (kW/C)',
           ax = ax,
           legend = True,
           legend_kwds = {'label':'kW/'+degree_sign+'C'},
           cmap = 'inferno_r',
           vmin=vmin,
           vmax=vmax,
           missing_kwds={'color': 'lightgrey'})
# plt.title('Mean gas heating losses')
plt.axis("off")
plt.savefig('Plots/Gas heating losses.jpg', dpi=2000)

#%% save files

# remove duplicate columns
LSOAs_no_duplicates = LSOAs.loc[:,~LSOAs.columns.duplicated()].copy()
DZs_no_duplicates = DZs.loc[:,~DZs.columns.duplicated()].copy()

LSOAs_no_duplicates.to_file('Resources/LSOA_gas_heat_loss_2017-2021.geojson',driver='GeoJSON',
                            index=True)
DZs_no_duplicates.to_file('Resources/DZ_gas_heat_loss_2017-2021.geojson',driver='GeoJSON',
                          index=True)

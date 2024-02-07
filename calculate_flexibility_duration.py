# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 12:10:43 2024

@author: Claire Halloran, University of Oxford

Calculates weather-dependent flexibility duration in comfortable heat-free hours
based on different percentile historical winter temperatures using the thermal
time constant for each region.

"""

import geopandas as gpd
import matplotlib.pyplot as plt
import math
import xarray as xr
from calculate_regional_HDDs import assign_gridded_values_to_regions

def calculate_heat_free_hours(gdf,temperature_column,initial_temp=21.,final_temp=18.):
    '''
    calculate comfortable heat-free hours based on Newton's law of cooling.

    Parameters
    ----------
    gdf : geodataframe
        geodataframe including 'Thermal time constant [h]' column.
    temperature_column : str
        name of column in gdf with outdoor temperature.
    initial_temp : float, optional
        initial indoor temperature. The default is 21..
    final_temp : TYPE, optional
        final indoor temperature. The default is 18..

    Returns
    -------
    gdf : geodataframe
        geodataframe with heat-free hours column added.

    '''
    gdf[temperature_column + ' heat-free hours']=[-gdf.at[region,'Thermal time constant [h]']*\
        math.log((final_temp-gdf.at[region, temperature_column]
                  )/(initial_temp-gdf.at[region, temperature_column])) for region in gdf.index]
    return gdf
    
def map_heat_free_hours(gdf, heat_free_hours_column, vmin, vmax, cmap='inferno'):
    fig, ax = plt.subplots()
    regions.plot(column = heat_free_hours_column,
             ax = ax,
             legend= True,
             legend_kwds = {'label':'Heat-free hours'},
             cmap = cmap,
             vmin=vmin,
             vmax=vmax,
             missing_kwds={'color': 'lightgrey'})
    plt.axis("off")
    plt.savefig(f'Plots/{heat_free_hours_column}.jpg', dpi=1000)

def colormap_histogram(series, vmin, vmax, ax, cmap = plt.cm.inferno):
    n, bins, patches = ax.hist(
        series,
        bins= 50,
        range = [vmin,vmax]
        )
    
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    col = bin_centers - min(bin_centers)
    col /= max(col)
    
    for c, p in zip(col, patches):
        plt.setp(p, 'facecolor', cmap(c))

# import regions with thermal time constants
regions = gpd.read_file('Resources/regional_thermal_time_constants.geojson',driver='GeoJSON')
regions.set_index('index', inplace=True)

# import temperature data
min_temperature = xr.open_mfdataset('Data/tasmin/*.nc')
max_temperature = xr.open_mfdataset('Data/tasmax/*.nc')
mean_temperature = (max_temperature['tasmax'] + min_temperature['tasmin'])/2

#%% identify heating season quantiles and how flexibility varies with each

# only include winter months (December to January)
heating_season_temperature = mean_temperature[(mean_temperature.time.dt.month>=12) | (mean_temperature.time.dt.month<=2)]
heating_season_temperature = heating_season_temperature.chunk(dict(time=-1))

coldest_temperature = heating_season_temperature.min(dim='time',skipna=False)
fifth_percentile = heating_season_temperature.quantile(0.05,dim='time',skipna=False,keep_attrs=True)
first_quartile = heating_season_temperature.quantile(0.2,dim='time',skipna=False,keep_attrs=True)
second_quartile = heating_season_temperature.quantile(0.4,dim='time',skipna=False,keep_attrs=True)
third_quartile = heating_season_temperature.quantile(0.6,dim='time',skipna=False,keep_attrs=True)
fourth_quartile = heating_season_temperature.quantile(0.8,dim='time',skipna=False,keep_attrs=True)
warmest_temperature = heating_season_temperature.max(dim='time',skipna=False)


#%% assign mean temperature on coldest and typical winter days to regions

regions = assign_gridded_values_to_regions(coldest_temperature, 'Coldest temperature', regions)
regions = assign_gridded_values_to_regions(fifth_percentile, 'Fifth percentile temperature', regions)
regions = assign_gridded_values_to_regions(first_quartile, 'First quartile temperature', regions)
regions = assign_gridded_values_to_regions(second_quartile, 'Second quartile temperature', regions)
regions = assign_gridded_values_to_regions(third_quartile, 'Third quartile temperature', regions)
regions = assign_gridded_values_to_regions(fourth_quartile, 'Fourth quartile temperature', regions)
regions = assign_gridded_values_to_regions(warmest_temperature, 'Warmest temperature', regions)


#%% calculate comfortable heat-free hours
regions = calculate_heat_free_hours(regions,'Coldest temperature')
regions = calculate_heat_free_hours(regions,'Fifth percentile temperature')
regions = calculate_heat_free_hours(regions,'First quartile temperature')
regions = calculate_heat_free_hours(regions,'Second quartile temperature')
regions = calculate_heat_free_hours(regions,'Third quartile temperature')
regions = calculate_heat_free_hours(regions,'Fourth quartile temperature')

# uniform 0 C outdoor temperature
regions['Comfortable heat-free hours']=-regions['Thermal time constant [h]']*math.log((18-5)/(21-5))


#%% map comfortable heat-free hours
vmin = min(regions['Coldest temperature heat-free hours'].quantile(0.01),
           regions['Fifth percentile temperature heat-free hours'].quantile(0.01),
           regions['First quartile temperature heat-free hours'].quantile(0.01),
           regions['Second quartile temperature heat-free hours'].quantile(0.01),
           regions['Third quartile temperature heat-free hours'].quantile(0.01),
           regions['Fourth quartile temperature heat-free hours'].quantile(0.01),
           regions['Comfortable heat-free hours'].quantile(0.01))

vmax = max(regions['Coldest temperature heat-free hours'].quantile(0.99),
           regions['Fifth percentile temperature heat-free hours'].quantile(0.99),
           regions['First quartile temperature heat-free hours'].quantile(0.99),
           regions['Second quartile temperature heat-free hours'].quantile(0.99),
           regions['Third quartile temperature heat-free hours'].quantile(0.99),
           regions['Fourth quartile temperature heat-free hours'].quantile(0.99),
           regions['Comfortable heat-free hours'].quantile(0.99))

map_heat_free_hours(regions, 'Comfortable heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'Coldest temperature heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'Fifth percentile temperature heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'First quartile temperature heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'Second quartile temperature heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'Third quartile temperature heat-free hours', vmin, vmax)
map_heat_free_hours(regions, 'Fourth quartile temperature heat-free hours', vmin, vmax)

#%% plot histogram of comfortable heat-free hours

mean_coldest_temperature = round(regions['Coldest temperature'].mean(),1) 
mean_fifth_percentile_temperature = round(regions['Fifth percentile temperature'].mean(),1)
mean_first_quartile_temperature = round(regions['First quartile temperature'].mean(),1)
mean_second_quartile_temperature = round(regions['Second quartile temperature'].mean(),1)
mean_third_quartile_temperature = round(regions['Third quartile temperature'].mean(),1)
mean_fourth_quartile_temperature = round(regions['Fourth quartile temperature'].mean(),1)


fig, ax = plt.subplots(6, figsize=[4,7], sharex=True, sharey = True,constrained_layout = True)

colormap_histogram(regions['Coldest temperature heat-free hours'], vmin, vmax, ax[0])
colormap_histogram(regions['Fifth percentile temperature heat-free hours'], vmin, vmax, ax[1])
colormap_histogram(regions['First quartile temperature heat-free hours'], vmin, vmax, ax[2])
colormap_histogram(regions['Second quartile temperature heat-free hours'], vmin, vmax, ax[3])
colormap_histogram(regions['Third quartile temperature heat-free hours'], vmin, vmax, ax[4])
colormap_histogram(regions['Fourth quartile temperature heat-free hours'], vmin, vmax, ax[5])


ax[5].set_xlabel('Heat-free hours')
ax[3].set_ylabel('Count of regions')

ax[0].set_title(f'Lowest temperature (mean = {mean_coldest_temperature}°C)',fontsize='medium')
ax[1].set_title(f'5th percentile temperature (mean = {mean_fifth_percentile_temperature}°C)',fontsize='medium')
ax[2].set_title(f'20th percentile temperature (mean = {mean_first_quartile_temperature}°C)',fontsize='medium')
ax[3].set_title(f'40th percentile temperature (mean = {mean_second_quartile_temperature}°C)',fontsize='medium')
ax[4].set_title(f'60th percentile temperature (mean = {mean_third_quartile_temperature}°C)',fontsize='medium')
ax[5].set_title(f'80th percentile temperature (mean = {mean_fourth_quartile_temperature}°C)',fontsize='medium')


ax[0].grid(True)
ax[1].grid(True)
ax[2].grid(True)
ax[3].grid(True)
ax[4].grid(True)
ax[5].grid(True)


plt.savefig('Plots/all heat-free hours histogram.jpg', dpi=300)
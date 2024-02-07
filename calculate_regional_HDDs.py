#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 4 14:53:34 2023

@author: Claire Halloran, University of Oxford

Calculates gridded historical HDDs for years used in spatial gas consumption 
statistics and assigns them to regions.

"""

import pandas as pd
import matplotlib.pyplot as plt
import rasterio
import os
import geopandas as gpd
import xarray as xr

def HDDs(T, threshold):
    '''
    calculate HDDs from HadUK-Grid observations

    Parameters
    ----------
    T : XArray DataSet
        temperature dataset.
    threshold : float
        threshold temperature for HDD calculation.

    Returns
    -------
    HDD : XArray Dataset
        total HDDs for the time period of the temperature dataset.

    '''
    difference = (threshold - T)
    difference = difference.clip(min=0.0)
    HDD = difference.sum(dim = 'time', skipna = False)
    return HDD

def fill_na_with_neighboring_mean(gdf, value_col):
    for region in gdf[gdf[value_col].isna()].index:
        neighbors = gdf[gdf.geometry.touches(gdf.loc[region,:].geometry)]
        neighboring_mean = neighbors[value_col].mean()
        gdf.at[region,value_col] = neighboring_mean
    return gdf


def assign_gridded_values_to_regions(HDD_DataArray, HDD_label, regions_gdf, crs='EPSG:27700'):
    '''
    assigns gridded values from a 2D dataarray to polygon regions

    Parameters
    ----------
    HDD_DataArray : Xarray DataArray
        2D grid of data.
    HDD_label : string
        label for data in regional geodataframe.
    regions_gdf : geodataframe
        geodataframe including geometry for regions.
    crs : string, optional
        Coordinate reference system string for gridded data. The default is 'EPSG:27700'.

    Returns
    -------
    regions_gdf : geodataframe
        geodataframe with temperature assigned to each region.

    '''
        
    # create a raster of temperature
    HDD_DataArray.rio.write_crs(crs, inplace = True)
    HDD_DataArray.rio.set_spatial_dims(x_dim='projection_x_coordinate',
                                          y_dim='projection_y_coordinate', inplace = True)
    filename = 'Resources/'+HDD_label+'.tif'
    try:
        os.remove(filename)
    except OSError:
        pass

    HDD_DataArray.rio.to_raster(filename)
    old_tif = rasterio.open(filename)
    
    regions_points = regions_gdf['geometry'].representative_point()
    regions_coord_list = [(x, y) for x, y in zip(regions_points.x, regions_points.y)]
    regions_gdf[HDD_label] = [x for x in old_tif.sample(regions_coord_list)]
    regions_gdf = regions_gdf.explode(HDD_label)
    regions_gdf[HDD_label]=pd.to_numeric(regions_gdf[HDD_label])
    
    # check if any representative points are outside of HadUK-Grid
    # and use means from neighboring LSOAs/DZs if so
    while regions_gdf[HDD_label].isna().sum()>0:
        regions_gdf = fill_na_with_neighboring_mean(regions_gdf, HDD_label)
        print('Replacing NaNs')
    return regions_gdf


if __name__ == "__main__":
    
    #%% try using HadUK-Grid 1 x 1 km observations
    # note these are in OSGB coordinates
    
    min_temperature = xr.open_mfdataset('Data/tasmin/*.nc')
    max_temperature = xr.open_mfdataset('Data/tasmax/*.nc')

    mean_temperature = (max_temperature['tasmax'] + min_temperature['tasmin'])/2
    
    #%% importing boundaries
    DZs = gpd.read_file('Data/SG_DataZoneBdry_2011/SG_DataZone_Bdry_2011.shp')
    LSOAs = gpd.read_file('Data/Lower_Layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Extent_BFE_EW_V3_2022_-4926191891001926707.geojson')
    DZs.set_index('Name', inplace = True)
    LSOAs.set_index('LSOA11NM', inplace = True)
    
    #%% calculating HDDs
    
    gas_years = [2017,2018,2019,2020,2021]
    
    gas_year_ranges = {
        '2017':slice('2017-06-15','2018-06-15'),
        '2018':slice('2018-05-15','2019-05-15'),
        '2019':slice('2019-05-15','2020-05-15'),
        '2020':slice('2020-05-15','2021-05-15'),
        '2021':slice('2021-05-15','2022-05-15'),
        }
    
    for year in gas_years:
        fuel_cutout = mean_temperature.sel(time = gas_year_ranges[f'{year}'])
        fuel_HDDs = HDDs(fuel_cutout, threshold = 15.5)       
        LSOAs = assign_gridded_values_to_regions(fuel_HDDs, f'{year} gas HDDs', LSOAs)
        DZs = assign_gridded_values_to_regions(fuel_HDDs, f'{year} gas HDDs', DZs)

        #%% plot sum of HDDs in each LSOA
        
        vmin = min(LSOAs[f'{year} gas HDDs'].quantile(0.005),DZs[f'{year} gas HDDs'].quantile(0.005))
        vmax=max(LSOAs[f'{year} gas HDDs'].quantile(0.995),DZs[f'{year} gas HDDs'].quantile(0.995))
        
        fig, ax = plt.subplots()
        LSOAs.plot(column = f'{year} gas HDDs', 
                   ax=ax,
                   cmap='coolwarm_r',
                    vmin=vmin,
                    vmax=vmax,
                   categorical=False)
        DZs.plot(column = f'{year} gas HDDs', 
                 legend=True,
                 legend_kwds = {'label':'HDDs'},
                   ax=ax,
                   cmap='coolwarm_r',
                   vmin=vmin,
                   vmax=vmax
                   )
        plt.title(f'gas HDDs {year}')
        plt.axis("off")
        plt.savefig(f'Plots/gas HDDs {year}.jpg', dpi=300)
            
        #%% save LSOAs and DZs with HDDs
        
    LSOAs.to_file('Resources/LSOA_HDDs_2010-2022.geojson',driver='GeoJSON')
    DZs.to_file('Resources/DZ_HDDs_2010-2022.geojson',driver='GeoJSON')

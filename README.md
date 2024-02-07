# GeoHeatFlex: Quantify geospatial heating flexibility

GeoHeatFlex is an open-source tool for quantifying heating flexibility potential in a building stock at high spatial resolution based on heating consumption data. This model uses high resolution heating consumption data, historical temperature data, and building size data. An example case study for gas-heated homes in Britain is included, but the model can be generalized to any region where similar data is available.
## Licenses and citation

GeoHeatFlex is distributed under the MIT license. Please note that the data used in this model have different licenses.

When you use GeoHeatFlex, please cite the forthcoming paper:
- Claire Halloran, Jesus Lizana, Malcolm McCulloch, Quantifying space heating flexibility potential at high spatial resolution with heating  consumption data.

## Setup

Clone the GeoHeatFlex repository using the following command in your terminal:
```
/some/other/path % cd /some/path

/some/path % git clone https://github.com/clairehalloran/GeoHeatFlex.git
```

Install the python dependencies using the package manager of your choice. When using `conda`, enter the following commands in your terminal to install and activate the environment:

```
.../GeoHeatFlex % conda env create -f environment.yaml
.../GeoHeatFlex % conda activate GeoHeatFlex
```
## Input data
All input data should be put in the `Data` folder. To recreate the case study for gas-heated houses, include the following data:
- HadGrid-UK minimum and maximum daily temperature observations for 2010-2022 in the `Data/tasmin` and `Data/tasmax` folders, respectively. These data are available in the [CEDA Archive](https://catalogue.ceda.ac.uk/uuid/4dc8450d889a491ebb20e724debe2dfb) under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- DataZone boundaries 2011 shapefile folder `Data/SG_DataZoneBdry_2011` available from [SpatialData.gov.scot](https://spatialdata.gov.scot/geonetwork/srv/eng/catalog.search#/metadata/7d3e8709-98fa-4d71-867c-d5c8293823f2) under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Lower Layer Super Output Areas (LSOA) boundaries 2011 `Data/Lower_Layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Extent_BFE_EW_V3_2022_-4926191891001926707.geojson`, available from the [UK Office for National Statistics Open Geography portalx](https://geoportal.statistics.gov.uk/datasets/ons::lower-layer-super-output-areas-dec-2011-boundaries-full-extent-bfe-ew-v3/explore) under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- LSOA domestic gas 2010 to 2021 `Data/LSOA_domestic_gas_2010-21.xlsx`, available from the [UK Department for Energy Security and Net Zero](https://www.gov.uk/government/statistics/lower-and-middle-super-output-areas-gas-consumption), available under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Energy Consumption in the UK 2022 End Use Tables `Data/ECUK_2022_End_Use_tables_27102022.xlsx`, available from available from the [UK Department for Energy Security and Net Zero](https://www.gov.uk/government/statistics/energy-consumption-in-the-uk-2022), available under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Census 2011 Table QS407EW: Number of rooms for England and Wales `Data/England_and_Wales_census_2011_number_of_rooms.csv` by 2011 LSOA. This Office for National Statistics data is available on [nomis](https://www.nomisweb.co.uk/census/2011/qs407ew) under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- Census 2011 Table QS407S: Number of rooms for Scotland, `Data/Scotland_census_2011_number_of_rooms.xlsx` by 2011 Data Zone, available from [Scotland's Census](https://www.scotlandscensus.gov.uk/search-the-census#/search-by) under the [Open Government License](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Search for "QS407SC" to find this table.
- Electrification of Heat trial heat pump performance cleansed data in `Data/Electrification of Heat/Dataset 1` and `Data/Electrification of Heat/Dataset 2`.  These datasets are available from the [UK Data Service](https://beta.ukdataservice.ac.uk/datacatalogue/doi/?id=9050#!#1) under the [Open Government License v2.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/).
- EPC-based thermal building characteristics for LSOAs in England and Wales by Alexandre Canet at Cardiff University in the `Data/UKERC` available from the [UKERC Energy Data Centre](https://ukerc.rl.ac.uk/cgi-bin/dataDiscover.pl?Action=detail&dataid=65bde35e-fdfe-452a-b00d-0ac9989ef41e) under a [CC-BY](https://creativecommons.org/licenses/by/4.0/) license.

## Running the model
The model is run with the following workflow:
### Heating degree days

The heating degree days for the time period that heating consumption is reported are calculated in the `calculate_regional_HDDs.py` script.
### Heat loss rate
Heat losses are calculated in the `calculate_heating_losses.py` script.
### Heat capacity & thermal time constants
Heat capacity and thermal time constants are calculated in the `calculate_time_constants.py` script. This script also saves the total thermal energy storage capacity in each region.
### Heating flexibility duration
The heating flexibility duration as measured by the number of comfortable heat-free hours is calculated in the `calculate_flexibility_duration.py` script.
### Validating time constant
Time constants based on an exponential fit of indoor temperature drop for homes in the Electrification of Heat Trial are calculated in the `EoH_time_constants.py` script.

The time constants calculated in GeoHeatFlex are compared with those obtained with the energy performance certificate-based method introduced by [Canet and Qadrdan](https://doi.org/10.1016/j.apenergy.2023.121616) and the indoor temperature-based method in the `validate_time_constants.py` script.
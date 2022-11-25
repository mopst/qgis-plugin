## Input File Specification

This plugin makes use of a range of input files. The files in [demo.zip](https://github.com/mopst/qgis-plugin/releases/download/v1.0.0/demo.zip) are in this required format. The requirements are detailed below.

- All files must cover the same geographic areas
- All files must be in the same coordinate system 

### Land Cover (Shapefile)
- *Example is brighton-lewes-down-land-cover.shp*
- This file contains the different land cover types. 
- The column specifying the type of land cover must be called **Main_habit**. 
- All land cover types must be present. 


### Land Cover Sensitivity (CSV File)
- *Example is land-cover-senstivity.csv*
- All land covers must be listed.
- If the land cover is not needed in the model, it must still be listed, and given a senstivity score of 1. 
- The land cover column must be called **Habitat_environment_type**. 


### Seasonality Score (CSV File)
- *Example is seasonality.csv*
- Contains information on which land cover types are more sensitive in summer or winter. 
- All land covers must be listed.
- The column specifying the type of land cover must be called **Habitat_environment_type**. 
- The two seasons are **Winter** and **Summer**, the columns must be called **Winter** and **Summer**. 
- Give each land cover a weight of **1** (No, i.e. not more sensitive in that season) or **2** (Yes, i.e. more sensitive in that season). 
- If a land cover type is not more sensitive in either season, label both as **1**. 
- If null values are present, then these land cover types will be missing in the **summer_raster** and **winter_raster** outputs. 

### Pressure Raster Layer & Opportunity Raster Layer
- *Example is bldbr-pressures-merged.tif & bldbr-opportunity-merged.tif*
- These identify the stakeholder identification of areas of tourism pressure and opportunity. 
- All rasters must be set to the same resolution and extent. 
- They must have values of **1** (there is pressure/opportunity) or **0** (there is not pressure/opportunity). 
- The pressure raster is used as a template (extent and resolution) for raster export of land cover for winter and summer. 

### Factor Weights (CSV File)
- *Example is factor-weights.csv*
- This lists all of the Factor Raster Layers and the weights given to them for Pressure and Opportunity. 
- **factor-file** column lists the file name (including extension). 
- **pressure-weight** lists the pressure weight. 
- **opportunity-weight** lists the opportunity weight. 

### Scenario Weights (CSV File)
- *Example is scenario-weights.csv*
- This lists the scenarios (three in the example, Profit, Business as usual, Custodianship) and their weights
- Structured with 4 columns (**scenario, factor-file, opportunity-multiplier, pressure-multiplier**)
- Each factor layer (with multiplier) must be listed for each scenario. 
- The example scenarios are Profit, Business as usual, Custodianship but these can be edited.  
- All factor layers must be present for each scenario, with an appropriate weighting for opportunity and pressure. A weighting of **1** will have no impact on the output. 


### Factor Raster Layers
- *Examples are in \factor-rasters*
- For ease, these are all stored within the **factor-rasters** sub-folder and can be added in using the browse tool or by selecting from the drop down list. 
- Rasters must have a value of **1** where the object is present, and **0** where the object is not present. 
- All rasters must have the same extent and resolution. 
- Rasters (filenames including extension) and factor weights must be listed in factor-weights.csv file. 
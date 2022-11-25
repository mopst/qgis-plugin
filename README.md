# MOPST QGIS Plugin
Version of the MOPST (Mapping Opportunity & Pressures for Sustainable Tourism) tool for QGIS, running as a QGIS Plugin.

## Requirements

This needs **QGIS 3.22** or greater to run.

This has been tested on QGIS 3.22 and should work on later versions of QGIS (it has also been tested on 3.30). It may also work on earlier versions of QGIS (3.x) but this has not been tested. *Please let us know if it works for you*. 

## Quick Setup & Demo Data

There is some demonstration data so you can test out the Toolbox on your computer. 

- Download the [MOPST QGIS Plugin](https://github.com/mopst/qgis-plugin/archive/refs/tags/v1.0.0.zip). Save this somewhere on your machine you can find it (e.g. Downloads). 
- Install the plugin by extracting the `qgis-plugin-1.0.0.zip` file in to your Plugins folder (`C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`).
- Open QGIS.
- Download the [`demo.zip`](https://github.com/mopst/qgis-plugin/releases/download/v1.0.0/demo.zip) file and extract it. This contains all the files you need to run the Plugin. 
- Open the `demo-project.qgz` file. 
- In the Processing Toolbox, navigate **MOPST > Analysis > MOPST**. 
- Set the input files, [like this image](demo-MOPST-plugin-inputs.png). 
- Click **OK** to run the model.
- Wait for model to run (about 2 minutes or so). 
- Check the outputs in whichever output directory you chose. 
- Compare these and the output log to the files available in the [`output.zip`](https://github.com/mopst/qgis-plugin/releases/download/v1.0.0/output.zip) file. 


For more details, please look at the [video](https://youtu.be/oK67PIRi64o) or the [Demonstration Files](demo.md) page. 
 
 
## Useful Information

It is helpful if all the layers needed for the tool (apart from raster factors) are added to QGIS Project before running the script. 
  
  
## Input File Specification

This toolbox makes use of a range of input files. The files in (demo) are in this required format. The requirements are summarised below. See [input-file-specification](input-file-specification.md) for more details. 

- All files must cover the same geographic areas
- All files must be in the same coordinate system 

Name (Format) | Example Filename | Description
-- | -- | -- 
Land Cover (Shapefile) | *brighton-lewes-down-land-cover.shp* | Shapefile of the different land cover types. 
Land Cover Sensitivity (CSV File) | *land-cover-sensitivity.csv* | Sensitivity score for each land cover type.
Seasonality Score (CSV File) | *seasonality.csv* | Contains information on which land cover types are more sensitive in summer or winter. 
Pressure Raster Layer (Raster TIF) | *bldbr-pressures-merged.tif* | Identify the stakeholder identification of areas of tourism pressure. 
Opportunity Raster Layer (Raster TIF) | *bldbr-opportunity-merged.tif* | identify the stakeholder identification of areas of tourism opportunity. 
Factor Weights (CSV File) | *seasonality.csv* | Lists all of the Factor Raster Layers and the weights given to them for Pressure and Opportunity.
Scenario Weights (CSV File) | *scenario-weights.csv* | lists the three scenarios (Profit, Business as usual, Custodianship) and their weights. 
Factor Raster Layers (Raster TIF) | *factor-rasters* | show the presence (**1**) or absence (**0**) of a range of factors. 
  
 
## Output Files:

The exported files (total number = 24) are stored in the output folder you choose in the Plugin. They are:

Filename | Output or working file? | Description
-- | -- | --
base-landcover.tif | Working file | 
opportunity-summer.tif | Working file | 
opportunity-winter.tif | Working file | 
pressure-summer.tif | Working file | 
pressure-winter.tif | Working file | 
summer_landcover.tif | Working file |
winter_landcover.tif | Working file |
scenario-Business as usual\opportunity-summer.tif | Output file | Summer Opportunity file for business scenario | 
scenario-Business as usual\opportunity-winter.tif | Output file | Winter Opportunity file for business scenario | 
scenario-Business as usual\pressure-summer.tif | Output file | Summer Pressure file for business scenario | 
scenario-Business as usual\pressure-winter.tif | Output file | Winter Pressure file for business scenario | 
scenario-Custodianship\opportunity-summer.tif | Output file | Summer Opportunity file for custodianship scenario | 
scenario-Custodianship\opportunity-winter.tif | Output file | Winter Opportunity file for custodianship scenario | 
scenario-Custodianship\pressure-summer.tif | Output file | Summer Pressure file for custodianship scenario | 
scenario-Custodianship\pressure-winter.tif | Output file | Winter Pressure file for custodianship scenario | 
scenario-Profit\opportunity-summer.tif | Output file | Summer Opportunity file for profit scenario | 
scenario-Profit\opportunity-winter.tif | Output file | Winter Opportunity file for profit scenario | 
scenario-Profit\pressure-summer.tif | Output file | Summer Pressure file for profit scenario | 
scenario-Profit\pressure-winter.tif | Output file | Winter Pressure file for profit scenario | 

They are available in [`output.zip`](). 
 

## Comments / Feedback

Please do let me know if you have any comments / feedback, via email: [nick@geospatialtrainingsolutions.co.uk](mailto:nick@geospatialtrainingsolutions.co.uk), or please submit a Pull Request on GitHub. 
 
 
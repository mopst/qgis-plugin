# -*- coding: utf-8 -*-

import os
import shutil

from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingOutputMultipleLayers,
                      )
import processing

from mopst.tables import (FACTOR_WEIGHTS_HEADER,
                          FACTOR_WEIGHTS_DATA,
                          SCENARIO_WEIGHTS_HEADER,
                          SCENARIO_WEIGHTS_DATA,
                         )

pluginPath = os.path.dirname(__file__)


class MopstAlgorithm(QgsProcessingAlgorithm):

    LANDCOVER = "LAND_COVER"
    LANDCOVER_SENSITIVITY = "LANDCOVER_SENSITIVITY"
    SENSITIVITY_SCORE_FIELD = "SENSITIVITY_SCORE_FIELD"
    SEASONALITY_SCORE = "SEASONALITY_SCORE"
    PRESSURE_AREAS = "PRESSURE_AREAS"
    OPPORTUNITY_AREAS = "OPPORTUNITY_AREAS"
    FACTORS = "FACTORS"
    FACTOR_WEIGHTS = "FACTOR_WEIGHTS"
    SCENARIO_WEIGHTS = "SCENARIO_WEIGHTS"
    OUTPUT = "OUTPUT"
    OUTPUT_LAYERS = "OUTPUT_LAYERS"

    def name(self):
        return "mopst"

    def displayName(self):
        return "MOPST"

    def group(self):
        return "Analysis"

    def groupId(self):
        return "analysis"

    def tags(self):
        return ["tourism", "opportunity", "pressures"]

    def shortHelpString(self):
        return "Performs MOPST (Mapping Opportunity & Pressures for Sustainable Tourism) analysis for given area."

    def helpUrl(self):
        return "http://github.com/mopst"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "logo.png"))

    def __init__(self):
        super().__init__()

    def createInstance(self):
        return type(self)()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.LANDCOVER, "Landcover",
                                                              [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.LANDCOVER_SENSITIVITY, "Landcover Sensitivity",
                                                              [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterField(self.SENSITIVITY_SCORE_FIELD, "Landcover sensitivity score",
                                                      None, self.LANDCOVER_SENSITIVITY))
        self.addParameter(QgsProcessingParameterFeatureSource(self.SEASONALITY_SCORE, "Seasonality score",
                                                              [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.PRESSURE_AREAS, "Pressure areas"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.OPPORTUNITY_AREAS, "Opportunity areas"))
        self.addParameter(QgsProcessingParameterMultipleLayers(self.FACTORS, "Factor rasters",
                                                               QgsProcessing.TypeRaster))
        self.addParameter(QgsProcessingParameterMatrix(self.FACTOR_WEIGHTS, "Factor weights", 9, False,
                                                       FACTOR_WEIGHTS_HEADER, FACTOR_WEIGHTS_DATA))
        self.addParameter(QgsProcessingParameterMatrix(self.SCENARIO_WEIGHTS, "Scenario weights", 69, False,
                                                       SCENARIO_WEIGHTS_HEADER, SCENARIO_WEIGHTS_DATA))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT, "Output directory"))
        self.addOutput(QgsProcessingOutputMultipleLayers(self.OUTPUT_LAYERS, "Output layers"))

    def processAlgorithm(self, parameters, context, feedback):
        fieldName = self.parameterAsString(parameters, self.SENSITIVITY_SCORE_FIELD, context)
        layer = self.parameterAsRasterLayer(parameters, self.PRESSURE_AREAS, context)
        factorLayers = self.parameterAsFileList(parameters, self.FACTORS, context)
        factorTable = self.parameterAsMatrix(parameters, self.FACTOR_WEIGHTS, context)
        scenarioTable = self.parameterAsMatrix(parameters, self.SCENARIO_WEIGHTS, context)
        self.outputDir = self.parameterAsString(parameters, self.OUTPUT, context)

        # convert lists into matrices (lists of lists)
        factorData = [factorTable[i:i + 3] for i in range(0, len(factorTable), 3)]
        scenarioData = [scenarioTable[i:i + 4] for i in range(0, len(scenarioTable), 4)]

        # create output directory if not exists
        os.makedirs(self.outputDir, exist_ok=True)

        self.layersToAdd = {"BASELINE":[]}

        # get names of the selected self.scenarios to avoid iterating
        # over the all self.scenarios every time. Also create output directories
        self.scenarios = []
        for i in scenarioData:
            if i[0] not in self.scenarios:
                self.scenarios.append(i[0])
                os.makedirs(os.path.join(self.outputDir, f"scenario-{i[0]}"), exist_ok=True)
                self.layersToAdd[i[0]] = []

        factorSteps = 4 + 8 * (len(factorLayers) - 1)
        nSteps = 8 + factorSteps + factorSteps * len(self.scenarios)

        multistepFeedback = QgsProcessingMultiStepFeedback(nSteps, feedback)
        step = 0

        outputs = {}
        self.outputLayers = []

        # convert landcover sensitivity score field to float
        feedback.pushInfo("Convert sensitivity score field to float.")
        params = {"INPUT": parameters[self.LANDCOVER_SENSITIVITY],
                  "FIELD": parameters[self.SENSITIVITY_SCORE_FIELD],
                  "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
        outputs["LCS_FLOAT"] = processing.run("qgis:texttofloat", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # join landcover layer with lancover sensitivity table
        feedback.pushInfo("Join landcover sensitivity table.")
        params = {"INPUT": parameters[self.LANDCOVER],
                  "FIELD": "Main_habit",
                  "INPUT_2": outputs["LCS_FLOAT"]["OUTPUT"],
                  "FIELD_2": "Habitat_environment_type",
                  "FIELDS_TO_COPY": [],
                  "METHOD": 1,
                  "DISCARD_NONMATCHING": False,
                  "PREFIX": "",
                  "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                  "NON_MATCHING": QgsProcessing.TEMPORARY_OUTPUT}
        outputs["JOIN_SENSITIVITY"] = processing.run("native:joinattributestable", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

        # TODO: check join errors

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # join seasonality table
        feedback.pushInfo("Join seasonality table.")
        params = {"INPUT": outputs["JOIN_SENSITIVITY"]["OUTPUT"],
                  "FIELD": "Main_habit",
                  "INPUT_2": parameters[self.SEASONALITY_SCORE],
                  "FIELD_2": "Habitat_environment_type",
                  "FIELDS_TO_COPY": [],
                  "METHOD": 1,
                  "DISCARD_NONMATCHING": False,
                  "PREFIX": "",
                  "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
                  "NON_MATCHING": QgsProcessing.TEMPORARY_OUTPUT}
        outputs["JOIN_SEASONALITY"] = processing.run("native:joinattributestable", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

        # TODO: check join errors

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # calculate summer sensitivity score
        feedback.pushInfo("Calculate summer sensitivity score.")
        params = {"INPUT": outputs["JOIN_SEASONALITY"]["OUTPUT"],
                  "FIELD_NAME": "summer_score",
                  "FIELD_TYPE": 0,
                  "FIELD_LENGTH": 18,
                  "FIELD_PRECISION": 11,
                  "FORMULA": f'"{fieldName}" * to_real("Summer")',
                  "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
        outputs["SUMMER_SCORE"] = processing.run("native:fieldcalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # calculate winter sensitivity score
        feedback.pushInfo("Calculate winter sensitivity score.")
        params = {"INPUT": outputs["SUMMER_SCORE"]["OUTPUT"],
                  "FIELD_NAME": "winter_score",
                  "FIELD_TYPE": 0,
                  "FIELD_LENGTH": 18,
                  "FIELD_PRECISION": 11,
                  "FORMULA": f'"{fieldName}" * to_real("Winter")',
                  "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
        outputs["WINTER_SCORE"] = processing.run("native:fieldcalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # rasterize base landcover sensitivity score using pressure raster as the template
        feedback.pushInfo("Rasterize base landcover.")
        params = {"INPUT": outputs["WINTER_SCORE"]["OUTPUT"],
                  "FIELD": parameters[self.SENSITIVITY_SCORE_FIELD],
                  "BURN": None,
                  "USE_Z": False,
                  "UNITS": 1,
                  "WIDTH": layer.rasterUnitsPerPixelX(),
                  "HEIGHT": layer.rasterUnitsPerPixelY(),
                  "EXTENT": parameters[self.PRESSURE_AREAS],
                  "NODATA": None,
                  "OPTIONS": "",
                  "DATA_TYPE": 5,
                  "INIT": None,
                  "INVERT": False,
                  "OUTPUT": os.path.join(self.outputDir, "base_landcover.tif")}
        outputs["LANDCOVER_BASE"] = processing.run("gdal:rasterize", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
        self.outputLayers.append(outputs["LANDCOVER_BASE"]["OUTPUT"])
        self.layersToAdd["BASELINE"].append(outputs["LANDCOVER_BASE"]["OUTPUT"])

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # rasterize summer landcover sensitivity score using pressure raster as the template
        feedback.pushInfo("Rasterize summer landcover.")
        params = {"INPUT": outputs["WINTER_SCORE"]["OUTPUT"],
                  "FIELD": "summer_score",
                  "BURN": None,
                  "USE_Z": False,
                  "UNITS": 1,
                  "WIDTH": layer.rasterUnitsPerPixelX(),
                  "HEIGHT": layer.rasterUnitsPerPixelY(),
                  "EXTENT": parameters[self.PRESSURE_AREAS],
                  "NODATA": None,
                  "OPTIONS": "",
                  "DATA_TYPE": 5,
                  "INIT": None,
                  "INVERT": False,
                  "OUTPUT": os.path.join(self.outputDir, "summer_landcover.tif")}
        outputs["LANDCOVER_SUMMER"] = processing.run("gdal:rasterize", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
        self.outputLayers.append(outputs["LANDCOVER_SUMMER"]["OUTPUT"])
        self.layersToAdd["BASELINE"].append(outputs["LANDCOVER_SUMMER"]["OUTPUT"])

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # rasterize winter landcover sensitivity score using pressure raster as the template
        feedback.pushInfo("Rasterize winter landcover.")
        params = {"INPUT": outputs["WINTER_SCORE"]["OUTPUT"],
                  "FIELD": "winter_score",
                  "BURN": None,
                  "USE_Z": False,
                  "UNITS": 1,
                  "WIDTH": layer.rasterUnitsPerPixelX(),
                  "HEIGHT": layer.rasterUnitsPerPixelY(),
                  "EXTENT": parameters[self.PRESSURE_AREAS],
                  "NODATA": None,
                  "OPTIONS": "",
                  "DATA_TYPE": 5,
                  "INIT": None,
                  "INVERT": False,
                  "OUTPUT": os.path.join(self.outputDir, "winter_landcover.tif")}
        outputs["LANDCOVER_WINTER"] = processing.run("gdal:rasterize", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
        self.outputLayers.append(outputs["LANDCOVER_WINTER"]["OUTPUT"])
        self.layersToAdd["BASELINE"].append(outputs["LANDCOVER_WINTER"]["OUTPUT"])

        step += 1
        multistepFeedback.setCurrentStep(step)
        if feedback.isCanceled():
            return {}

        # process factors
        for i, factorFile in enumerate(factorLayers):
            feedback.pushInfo(f"Process factor file {factorFile}.")

            fileName = os.path.split(factorFile)[1]

             # get pressure and opportunity weights for the factor
            found = False
            for f in factorData:
                if f[0] == fileName:
                    pressureWeight = f[1]
                    opportunityWeight = f[2]
                    found = True
                    break

            if not found:
                raise QgsProcessingException(f"Could not find pressure and opportunity weights for factor file {fileName}.")

            # baseline pressure summer factor
            params = {"INPUT_A": outputs["LANDCOVER_SUMMER"]["OUTPUT"],
                      "BAND_A": 1,
                      "FORMULA": f"A*{pressureWeight}",
                      "RTYPE": 5,
                      "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
            factor_pressure_summer = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

            step += 1
            multistepFeedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # baseline opportunity summer factor
            params = {"INPUT_A": outputs["LANDCOVER_SUMMER"]["OUTPUT"],
                      "BAND_A": 1,
                      "FORMULA": f"A*{opportunityWeight}",
                      "RTYPE": 5,
                      "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
            factor_opportunity_summer = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

            step += 1
            multistepFeedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # baseline pressure winter factor
            params = {"INPUT_A": outputs["LANDCOVER_WINTER"]["OUTPUT"],
                      "BAND_A": 1,
                      "FORMULA": f"A*{pressureWeight}",
                      "RTYPE": 5,
                      "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
            factor_pressure_winter = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

            step += 1
            multistepFeedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            # baseline opportunity winter factor
            params = {"INPUT_A": outputs["LANDCOVER_WINTER"]["OUTPUT"],
                      "BAND_A": 1,
                      "FORMULA": f"A*{opportunityWeight}",
                      "RTYPE": 5,
                      "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
            factor_opportunity_winter = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

            step += 1
            multistepFeedback.setCurrentStep(step)
            if feedback.isCanceled():
                return {}

            if i == 0:
                # if this is the first factor, we store calculated rasters as outputs
                outputs["BASELINE_PRESSURE_SUMMER"] = factor_pressure_summer["OUTPUT"]
                outputs["BASELINE_OPPORTUNITY_SUMMER"] = factor_opportunity_summer["OUTPUT"]
                outputs["BASELINE_PRESSURE_WINTER"] = factor_pressure_winter["OUTPUT"]
                outputs["BASELINE_OPPORTUNITY_WINTER"] = factor_opportunity_winter["OUTPUT"]
            else:
                # for 2nd and all subsequent factors we add them to the previously saved
                # outputs and then update output to point out at the new file

                # baseline pressure summer (all factors)
                params = {"INPUT_A": outputs["BASELINE_PRESSURE_SUMMER"],
                          "BAND_A": 1,
                          "INPUT_B": factor_pressure_summer["OUTPUT"],
                          "BAND_B": 1,
                          "FORMULA": f"A+B",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                outputs["BASELINE_PRESSURE_SUMMER"] = r["OUTPUT"]

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # baseline opportunity summer (all factors)
                params = {"INPUT_A": outputs["BASELINE_OPPORTUNITY_SUMMER"],
                          "BAND_A": 1,
                          "INPUT_B": factor_opportunity_summer["OUTPUT"],
                          "BAND_B": 1,
                          "FORMULA": f"A+B",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                outputs["BASELINE_OPPORTUNITY_SUMMER"] = r["OUTPUT"]

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # baseline pressure winter (all factors)
                params = {"INPUT_A": outputs["BASELINE_PRESSURE_WINTER"],
                          "BAND_A": 1,
                          "INPUT_B": factor_pressure_winter["OUTPUT"],
                          "BAND_B": 1,
                          "FORMULA": f"A+B",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                outputs["BASELINE_PRESSURE_WINTER"] = r["OUTPUT"]

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # baseline opportunity winter (all factors)
                params = {"INPUT_A": outputs["BASELINE_OPPORTUNITY_WINTER"],
                          "BAND_A": 1,
                          "INPUT_B": factor_opportunity_winter["OUTPUT"],
                          "BAND_B": 1,
                          "FORMULA": f"A+B",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                outputs["BASELINE_OPPORTUNITY_WINTER"] = r["OUTPUT"]

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

            # process user self.scenarios
            for s in self.scenarios:
                feedback.pushInfo(f"Process scenario '{s}'.")

                found = False
                for sw in scenarioData:
                    if sw[0] == s and sw[1] == fileName:
                        opportunityMultiplier = sw[2]
                        pressureMultiplier = sw[3]
                        found = True
                        break

                if not found:
                    raise QgsProcessingException(f"Could not find pressure and opportunity multipliers scenario {s} and factor file {fileName}.")

                # scenario pressure summer factor
                params = {"INPUT_A": factor_pressure_summer["OUTPUT"],
                          "BAND_A": 1,
                          "FORMULA": f"A*{pressureMultiplier}",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                scenario_pressure_summer = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # scenario opportunity summer factor
                params = {"INPUT_A": factor_opportunity_summer["OUTPUT"],
                          "BAND_A": 1,
                          "FORMULA": f"A*{opportunityMultiplier}",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                scenario_opportunity_summer = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # scenario pressure winter factor
                params = {"INPUT_A": factor_pressure_winter["OUTPUT"],
                          "BAND_A": 1,
                          "FORMULA": f"A*{pressureMultiplier}",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                scenario_pressure_winter = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                # scenario opportunity winter factor
                params = {"INPUT_A": factor_opportunity_winter["OUTPUT"],
                          "BAND_A": 1,
                          "FORMULA": f"A*{opportunityMultiplier}",
                          "RTYPE": 5,
                          "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                scenario_opportunity_winter = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)

                step += 1
                multistepFeedback.setCurrentStep(step)
                if feedback.isCanceled():
                    return {}

                if i == 0:
                    # if this is the first factor for current scenario, we just store rasters as outputs
                    outputs[f"{s}_PRESSURE_SUMMER"] = scenario_pressure_summer["OUTPUT"]
                    outputs[f"{s}_OPPORTUNITY_SUMMER"] = scenario_opportunity_summer["OUTPUT"]
                    outputs[f"{s}_PRESSURE_WINTER"] = scenario_pressure_winter["OUTPUT"]
                    outputs[f"{s}_OPPORTUNITY_WINTER"] = scenario_opportunity_winter["OUTPUT"]
                else:
                    # for 2nd and all subsequent factors we add them to the previously saved
                    # outputs and then update output to point out at the new file

                    # scenario pressure summer (all factors)
                    params = {"INPUT_A": outputs[f"{s}_PRESSURE_SUMMER"],
                              "BAND_A": 1,
                              "INPUT_B": scenario_pressure_summer["OUTPUT"],
                              "BAND_B": 1,
                              "FORMULA": f"A+B",
                              "RTYPE": 5,
                              "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                    r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                    outputs[f"{s}_PRESSURE_SUMMER"] = r["OUTPUT"]

                    step += 1
                    multistepFeedback.setCurrentStep(step)
                    if feedback.isCanceled():
                        return {}

                    # scenario opportunity summer (all factors)
                    params = {"INPUT_A": outputs[f"{s}_OPPORTUNITY_SUMMER"],
                              "BAND_A": 1,
                              "INPUT_B": scenario_opportunity_summer["OUTPUT"],
                              "BAND_B": 1,
                              "FORMULA": f"A+B",
                              "RTYPE": 5,
                              "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                    r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                    outputs[f"{s}_OPPORTUNITY_SUMMER"] = r["OUTPUT"]

                    step += 1
                    multistepFeedback.setCurrentStep(step)
                    if feedback.isCanceled():
                        return {}

                    # scenario pressure winter (all factors)
                    params = {"INPUT_A": outputs[f"{s}_PRESSURE_WINTER"],
                              "BAND_A": 1,
                              "INPUT_B": scenario_pressure_winter["OUTPUT"],
                              "BAND_B": 1,
                              "FORMULA": f"A+B",
                              "RTYPE": 5,
                              "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                    r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                    outputs[f"{s}_PRESSURE_WINTER"] = r["OUTPUT"]

                    step += 1
                    multistepFeedback.setCurrentStep(step)
                    if feedback.isCanceled():
                        return {}

                    # scenario opportunity winter (all factors)
                    params = {"INPUT_A": outputs[f"{s}_OPPORTUNITY_WINTER"],
                              "BAND_A": 1,
                              "INPUT_B": scenario_opportunity_winter["OUTPUT"],
                              "BAND_B": 1,
                              "FORMULA": f"A+B",
                              "RTYPE": 5,
                              "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
                    r = processing.run("gdal:rastercalculator", params, context=context, feedback=multistepFeedback, is_child_algorithm=True)
                    outputs[f"{s}_OPPORTUNITY_WINTER"] = r["OUTPUT"]

                    step += 1
                    multistepFeedback.setCurrentStep(step)
                    if feedback.isCanceled():
                        return {}

        # copy results to the output directory
        self.scenarios.append("BASELINE")
        for s in self.scenarios:
            dst = self.outputDir
            if s != "BASELINE":
                dst = os.path.join(self.outputDir, f"scenario-{s}")
            r = shutil.copyfile(outputs[f"{s}_PRESSURE_SUMMER"], os.path.join(dst, "pressure-summer.tif"))
            self.outputLayers.append(r)
            self.layersToAdd[s].append(r)
            r = shutil.copyfile(outputs[f"{s}_OPPORTUNITY_SUMMER"], os.path.join(dst, "opportunity-summer.tif"))
            self.outputLayers.append(r)
            self.layersToAdd[s].append(r)
            r = shutil.copyfile(outputs[f"{s}_PRESSURE_WINTER"], os.path.join(dst, "pressure-winter.tif"))
            self.outputLayers.append(r)
            self.layersToAdd[s].append(r)
            r = shutil.copyfile(outputs[f"{s}_OPPORTUNITY_WINTER"], os.path.join(dst, "opportunity-winter.tif"))
            self.outputLayers.append(r)
            self.layersToAdd[s].append(r)

        with open(os.path.join(self.outputDir, "execution-log.txt"), "w", encoding="utf-8") as f:
            f.write(feedback.textLog())

        return {self.OUTPUT: self.outputDir,
                self.OUTPUT_LAYERS: self.outputLayers}

    def postProcessAlgorithm(self, context, feedback):
        project = context.project()
        root = project.instance().layerTreeRoot()

        top_group = root.findGroup("Outputs")
        if not top_group:
            top_group = root.insertGroup(0, "Outputs")

        layers = top_group.findLayerIds()
        project.removeMapLayers(layers)

        for s in self.scenarios:
            if s == "BASELINE":
                group = top_group
            else:
                group = top_group.findGroup(s)
                if not group:
                    group = top_group.addGroup(s)

            for l in self.layersToAdd[s]:
                layer = QgsProcessingUtils.mapLayerFromString(l, context)
                if layer.isValid():
                    project.addMapLayer(layer, False)
                    group.addLayer(layer)

        return {self.OUTPUT: self.outputDir,
                self.OUTPUT_LAYERS: self.outputLayers}

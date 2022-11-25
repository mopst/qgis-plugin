# -*- coding: utf-8 -*-

import os

from qgis.core import QgsApplication

from mopst.provider import MopstProvider

pluginPath = os.path.dirname(__file__)


class MopstPlugin:

    def __init__(self):
        self.provider = MopstProvider()

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

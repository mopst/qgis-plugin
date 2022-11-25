# -*- coding: utf-8 -*-

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import QgsProcessingProvider

from mopst.algorithm import MopstAlgorithm

pluginPath = os.path.dirname(__file__)


class MopstProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        return "mopst"

    def name(self):
        return "MOPST"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "logo.png"))

    def load(self):
        self.refreshAlgorithms()
        return True

    def unload(self):
        pass

    def getAlgs(self):
        algs = [MopstAlgorithm(),
               ]

        return algs

    def loadAlgorithms(self):
        self.algs = self.getAlgs()
        for a in self.algs:
            self.addAlgorithm(a)

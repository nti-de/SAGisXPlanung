import os

import pytest

from qgis.PyQt.QtWidgets import QMenu, QToolBar
from qgis.core import QgsProject
from qgis.utils import iface
from SAGisXPlanung.XPlanungPlugin import XPlanung


class TestXPlanungPlugin_installation:
    @pytest.mark.skipif('CI' in os.environ, reason="stubs not available in pytest-qgis")
    def test_is_installed(self, mocker):
        mocker.patch(
            'SAGisXPlanung.gui.XPlanungDialog.QPlanComboBox.refresh',
            return_value=None
        )
        plugin = XPlanung(iface)
        plugin.initGui()
        assert iface.mainWindow().findChild(QMenu, 'sagis_menu')
        assert iface.mainWindow().findChild(QToolBar, 'sagis_toolbar')

    @pytest.mark.skipif('CI' in os.environ, reason="stubs not available in pytest-qgis")
    def test_unload(self, mocker):
        mocker.patch(
            'SAGisXPlanung.gui.XPlanungDialog.QPlanComboBox.refresh',
            return_value=None
        )
        plugin = XPlanung(iface)
        plugin.initGui()

        plugin.unload()

        with pytest.raises(TypeError):
            QgsProject.instance().homePathChanged.disconnect(plugin.onProjectLoaded)

        with pytest.raises(TypeError):
            iface.layerTreeView().layerTreeModel().rowsInserted.disconnect(plugin.onRowsInserted)


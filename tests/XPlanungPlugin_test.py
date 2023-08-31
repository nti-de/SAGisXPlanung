import pytest
from PyQt5.QtWidgets import QToolBar

from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsProject
from qgis.utils import iface, plugins, startPlugin

from SAGisXPlanung import classFactory


def setup_module(module):
    plugins['SAGisXPlanung'] = classFactory(iface)
    assert plugins['SAGisXPlanung']


class TestXPlanungPlugin_installation:

    def test_is_installed(self, mocker):
        mocker.patch(
            'SAGisXPlanung.gui.XPlanungDialog.QPlanComboBox.refresh',
            return_value=None
        )
        assert startPlugin('SAGisXPlanung')
        assert iface.mainWindow().findChild(QMenu, 'sagis_menu')
        assert iface.mainWindow().findChild(QToolBar, 'sagis_toolbar')

    def test_unload(self):
        plugins['SAGisXPlanung'].unload()

        with pytest.raises(TypeError):
            QgsProject.instance().homePathChanged.disconnect(plugins['SAGisXPlanung'].onProjectLoaded)

        with pytest.raises(TypeError):
            iface.layerTreeView().layerTreeModel().rowsInserted.disconnect(plugins['SAGisXPlanung'].onRowsInserted)


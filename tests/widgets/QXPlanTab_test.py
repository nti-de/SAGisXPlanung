from datetime import datetime

import pytest
from qgis.PyQt import QtWidgets, QtCore

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QComboBoxNoScroll, QDateEditNoScroll, QBooleanInput, QDateListInput
from SAGisXPlanung.gui.widgets.QXPlanScrollPage import QXPlanScrollPage
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget


@pytest.fixture()
def scroll_page(mocker):
    mocker.patch(
        'SAGisXPlanung.gui.widgets.QXPlanScrollPage.QAddRelationDropdown.refreshComboBox',
        return_value=None
    )
    page = QXPlanScrollPage(BP_Plan, None)
    return page


@pytest.fixture()
def tab_widget(mocker):
    mocker.patch(
        'SAGisXPlanung.gui.widgets.QXPlanScrollPage.QAddRelationDropdown.refreshComboBox',
        return_value=None
    )
    tab = QXPlanTabWidget(BP_Plan, None)
    return tab


class TestQXPlanScrollPage_createInput:

    @pytest.mark.parametrize('input_name,expected_control,required', [('ausfertigungsDatum', QDateEditNoScroll, False),
                                                                      ('rechtsstand', QComboBoxNoScroll, False),
                                                                      ('gruenordnungsplan', QBooleanInput, False),
                                                                      ('hoehenbezug', QtWidgets.QLineEdit, False),
                                                                      ('auslegungsStartDatum', QDateListInput, False),
                                                                      ('planArt', QComboBoxNoScroll, True)])
    def test_createInput(self, scroll_page, input_name, expected_control, required):
        _, control = scroll_page.createInput(input_name, BP_Plan)

        assert isinstance(control, expected_control)
        if required:
            assert input_name in scroll_page.required_inputs


class TestQXPlanScrollPage_getObjectFromInputs:

    def test_get_object(self, mocker, scroll_page):
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.query.return_value.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        keys = BP_Plan.__table__.columns.keys()
        for i, key in enumerate(keys):
            if "id" in key or "srs" in key:
                continue
            label, control = scroll_page.createInput(key, BP_Plan)

            if key == 'name':
                control.setText('test')
            elif key == 'erstellungsMassstab':
                control.setText('123')
            elif key == 'auslegungsStartDatum':
                control.setDefault('25.08.2021, 16.08.2021')

            if isinstance(control, QDateEditNoScroll):
                control.setDate(QtCore.QDate(2020, 6, 10))

            scroll_page.fields[key] = control

        assert scroll_page.fields
        plan = scroll_page.getObjectFromInputs(validate_forms=False)
        assert isinstance(plan, BP_Plan)

    # test causes strange segmentation fault ?
    # def test_addRelation(self, scroll_page, qtbot):
    #     widget = scroll_page.fields['gemeinde']
    #     assert widget
    #     qtbot.addWidget(widget)
    #     qtbot.mouseClick(widget.b_plus, QtCore.Qt.LeftButton, delay=1)


class TestQXPlanTabWidget_closeTab:

    def test_populateContent(self, tab_widget, mocker, qtbot):
        mocker.patch(
            'SAGisXPlanung.gui.widgets.QXPlanScrollPage.QXPlanScrollPage.validateForms',
            return_value=True
        )
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.query.return_value.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        qtbot.addWidget(tab_widget)

        # test adding tab
        group_box = tab_widget.widget(0).vBox.itemAt(0).widget()
        assert isinstance(group_box, QtWidgets.QGroupBox)
        add_button = [button for button in group_box.findChildren(QtWidgets.QPushButton)
                      if button.text() == 'Hinzufügen'][0]
        qtbot.mouseClick(add_button, QtCore.Qt.LeftButton)
        assert tab_widget.count() == 2

        # test populate content from multiple tabs
        obj = tab_widget.populateContent()
        assert obj

    def test_closeTab(self, tab_widget, qtbot):
        qtbot.addWidget(tab_widget)

        # add tab
        group_box = tab_widget.widget(0).vBox.itemAt(0).widget()
        assert isinstance(group_box, QtWidgets.QGroupBox)
        add_button = [button for button in group_box.findChildren(QtWidgets.QPushButton)
                      if button.text() == 'Hinzufügen'][0]
        qtbot.mouseClick(add_button, QtCore.Qt.LeftButton)

        # test closing tab
        close_button = tab_widget.tabBar().tabButton(1, QtWidgets.QTabBar.RightSide)
        assert close_button
        qtbot.mouseClick(close_button, QtCore.Qt.LeftButton)

        assert tab_widget.count() == 1

    # test causes strange segmentation fault ?
    # def test_closeTab_withDependencies(self, tab_widget, qtbot):
    #     qtbot.addWidget(tab_widget)
    #
    #     # add first tab
    #     group_box = tab_widget.widget(0).vBox.itemAt(0).widget()
    #     assert isinstance(group_box, QtWidgets.QGroupBox)
    #     add_button = [button for button in group_box.findChildren(QtWidgets.QPushButton)
    #                   if button.text() == 'Hinzufügen'][0]
    #     qtbot.mouseClick(add_button, QtCore.Qt.LeftButton)
    #
    #     # add dependent subrelation
    #     group_box = tab_widget.widget(1).vBox.itemAt(1).widget()
    #     assert isinstance(group_box, QtWidgets.QGroupBox)
    #     add_button = [button for button in group_box.findChildren(QtWidgets.QPushButton)
    #                   if button.text() == 'Hinzufügen'][0]
    #     qtbot.mouseClick(add_button, QtCore.Qt.LeftButton)
    #
    #     # test closing tab
    #     close_button = tab_widget.tabBar().tabButton(1, QtWidgets.QTabBar.RightSide)
    #     assert close_button
    #
    #     qtbot.mouseClick(close_button, QtCore.Qt.LeftButton)
    #     yes_button = tab_widget.close_warning.button(QtWidgets.QMessageBox.Yes)
    #     qtbot.mouseClick(yes_button, QtCore.Qt.LeftButton)


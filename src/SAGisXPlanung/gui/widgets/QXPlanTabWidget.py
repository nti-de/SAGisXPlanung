import itertools

from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import QtWidgets

from sqlalchemy import inspect

from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.XPlan.types import ConformityException, InvalidFormException
from SAGisXPlanung.gui.widgets.QXPlanScrollPage import QXPlanScrollPage


class QXPlanTabWidget(QtWidgets.QTabWidget):
    def __init__(self, main_type, parent_type=None, *args, **kwargs):
        super(QXPlanTabWidget, self).__init__(*args, **kwargs)
        self.main_type = main_type
        self.parent_type = parent_type
        self.close_warning = None

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(lambda index: self.closeTab(index))
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        if issubclass(self.parent_type, XP_Objekt):
            return

        self.createTab(self.main_type, parent=parent_type)

    def closeTab(self, index):
        tab_to_close: QXPlanScrollPage = self.widget(index)

        should_close = self.shouldCloseTab(tab_to_close)
        if not should_close:
            return

        # for all pages, check if current page is a child of page. if yes, enable button and remove from children
        for i in range(0, self.count()):
            if i == index:
                continue
            page: QXPlanScrollPage = self.widget(i)
            if tab_to_close in page.child_pages:
                button = page.fields[tab_to_close.parent_attribute]
                button.setEnabled(True)
                page.removeChildPage(tab_to_close)

        for child_page in tab_to_close.child_pages:
            self.removeTab(self.indexOf(child_page))
        self.removeTab(index)

    def shouldCloseTab(self, tab: QXPlanScrollPage) -> bool:
        # always close if no dependencies present
        if len(tab.child_pages) == 0:
            return True

        msg = f'Es gibt abhängige Objekte vom Typ <ul>'
        for child_page in tab.child_pages:
            msg += f"<li><code>{child_page.cls_type.__name__}</code></li>"
        msg += '</ul>Trotzdem löschen?'

        self.close_warning = QtWidgets.QMessageBox.information(self, f'{tab.cls_type.__name__} entfernen', msg,
                                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        return self.close_warning == QtWidgets.QMessageBox.Yes

    def createTab(self, cls, parent=None, parent_attribute=None, existing_xid=None, closable=False):
        scroll = QXPlanScrollPage(cls, parent, parent_attribute, existing_xid, widgetResizable=True)
        scroll.addRelationRequested.connect(
            lambda cls_type, uselist, attr: self.onAddRelationRequested(cls, cls_type, uselist, attr))
        scroll.parentLinkClicked.connect(self.onParentLinkClicked)
        scroll.requestPageToTop.connect(lambda: self.setCurrentWidget(self.sender()))

        if self.currentIndex() != -1:
            current_page: QXPlanScrollPage = self.widget(self.currentIndex())
            current_page.addChildPage(scroll)

        self.insertTab(self.currentIndex() + 1, scroll, cls.__name__)
        self.setCurrentIndex(self.currentIndex() + 1)

        if not closable:
            self.tabBar().tabButton(self.currentIndex(), QtWidgets.QTabBar.RightSide).resize(0, 0)

    def onAddRelationRequested(self, cls, cls_type, uselist, parent_attribute):
        tab_exists = any([self.widget(index).parent_attribute == parent_attribute for index in range(self.count())])
        if not uselist and tab_exists:
            return
        self.createTab(cls_type, parent=cls, parent_attribute=parent_attribute, closable=True)

    @pyqtSlot()
    def onParentLinkClicked(self):
        for i in range(0, self.count()):
            if i == self.currentIndex():
                continue
            page: QXPlanScrollPage = self.widget(i)
            if self.sender() in page.child_pages:
                self.setCurrentWidget(page)

    def populateContent(self):
        try:

            obj = self.widget(0).getObjectFromInputs()
            if hasattr(obj, 'validate'):
                obj.validate()

            self.populateRelations(obj)

            return obj
        except ConformityException as e:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)

            msg.setText(e.message)
            msg.setWindowTitle(f"Konformitätsbedingung {e.code} für das Objekt {e.object_type} verletzt")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            ret = msg.exec_()
        except InvalidFormException:
            pass

    def populateRelations(self, obj, is_subrel=False, parent_class=None, current_index=None):
        for rel in inspect(obj.__class__).relationships.items():
            if parent_class == rel[1].mapper.class_ or hasattr(obj, f'{rel[0]}_id'):
                continue

            if not is_subrel:
                tab_widgets = [self.widget(index) for index in range(self.count())
                               if rel[1].mapper.class_.__name__ == self.tabText(index)]
            else:
                tab_widgets = [self.widget(index) for index in
                               itertools.takewhile(lambda x: rel[1].mapper.class_.__name__ == self.tabText(x),
                                                   range(current_index + 1, self.count()))]
            for tab in tab_widgets:
                # check for correct tab, if multiple relations of same type are present
                if rel[0] != tab.parent_attribute:
                    continue

                relation = tab.getObjectFromInputs()
                if hasattr(relation, 'validate'):
                    relation.validate()

                # append or set data, depending on whether relation is one-to-one or one-to-many
                if rel[1].uselist:
                    getattr(obj, rel[0]).append(relation)
                else:
                    setattr(obj, rel[0], relation)

                i = self.indexOf(tab)
                self.populateRelations(relation, is_subrel=True, parent_class=tab.parent_class, current_index=i)

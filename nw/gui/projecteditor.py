# -*- coding: utf-8 -*-
"""novelWriter GUI Project Editor

 novelWriter – GUI Project Editor
===================================
 Class holding the project editor

 File History:
 Created: 2018-09-29 [0.0.1]

"""

import logging
import nw

from os import path

from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QIcon, QPixmap, QColor, QBrush, QStandardItemModel
from PyQt5.QtSvg     import QSvgWidget
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QPlainTextEdit, QLabel,
    QWidget, QTabWidget, QDialogButtonBox, QListWidget, QListWidgetItem, QPushButton,
    QColorDialog, QAbstractItemView, QTreeWidget, QTreeWidgetItem
)
from nw.enum import nwAlert

logger = logging.getLogger(__name__)

class GuiProjectEditor(QDialog):

    def __init__(self, theParent, theProject):
        QDialog.__init__(self, theParent)

        logger.debug("Initialising ProjectEditor ...")

        self.mainConf   = nw.CONFIG
        self.theParent  = theParent
        self.theProject = theProject
        self.outerBox   = QHBoxLayout()
        self.innerBox   = QVBoxLayout()

        self.setWindowTitle("Project Settings")

        self.gradPath = path.abspath(path.join(self.mainConf.appPath,"graphics","block.svg"))
        self.svgGradient = QSvgWidget(self.gradPath)
        self.svgGradient.setFixedWidth(80)

        self.theProject.countStatus()
        self.tabMain    = GuiProjectEditMain(self.theParent, self.theProject)
        self.tabStatus  = GuiProjectEditStatus(self.theParent, self.theProject.statusItems)
        self.tabImport  = GuiProjectEditStatus(self.theParent, self.theProject.importItems)
        self.tabReplace = GuiProjectEditReplace(self.theParent, self.theProject)

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.tabMain,   "Settings")
        self.tabWidget.addTab(self.tabStatus, "Status")
        self.tabWidget.addTab(self.tabImport, "Importance")
        self.tabWidget.addTab(self.tabReplace,"Auto-Replace")

        self.setLayout(self.outerBox)
        self.outerBox.addWidget(self.svgGradient)
        self.outerBox.addLayout(self.innerBox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self._doSave)
        self.buttonBox.rejected.connect(self._doClose)

        self.innerBox.addWidget(self.tabWidget)
        self.innerBox.addWidget(self.buttonBox)

        self.show()

        logger.debug("ProjectEditor initialisation complete")

        return

    def _doSave(self):
        logger.verbose("ProjectEditor save button clicked")

        projName    = self.tabMain.editName.text()
        bookTitle   = self.tabMain.editTitle.text()
        bookAuthors = self.tabMain.editAuthors.toPlainText()
        self.theProject.setProjectName(projName)
        self.theProject.setBookTitle(bookTitle)
        self.theProject.setBookAuthors(bookAuthors)

        if self.tabStatus.colChanged:
            statusCol = self.tabStatus.getNewList()
            self.theProject.setStatusColours(statusCol)
        if self.tabImport.colChanged:
            importCol = self.tabImport.getNewList()
            self.theProject.setImportColours(importCol)
        if self.tabStatus.colChanged or self.tabImport.colChanged:
            self.theParent.rebuildTree()
        if self.tabReplace.arChanged:
            newList = self.tabReplace.getNewList()
            self.theProject.setAutoReplace(newList)

        self.close()

        return

    def _doClose(self):
        logger.verbose("ProjectEditor close button clicked")
        self.close()
        return

# END Class GuiProjectEditor

class GuiProjectEditMain(QWidget):

    def __init__(self, theParent, theProject):
        QWidget.__init__(self, theParent)

        self.theParent   = theParent
        self.theProject  = theProject
        self.mainForm    = QFormLayout()
        self.editName    = QLineEdit()
        self.editTitle   = QLineEdit()
        self.editAuthors = QPlainTextEdit()

        self.mainForm.addRow("Working Title", self.editName)
        self.mainForm.addRow("Book Title",    self.editTitle)
        self.mainForm.addRow("Book Authors",  self.editAuthors)

        self.editName.setText(self.theProject.projName)
        self.editTitle.setText(self.theProject.bookTitle)
        bookAuthors = ""
        for bookAuthor in self.theProject.bookAuthors:
            bookAuthors += bookAuthor+"\n"
        self.editAuthors.setPlainText(bookAuthors)

        self.setLayout(self.mainForm)

        return

# END Class GuiProjectEditMain

class GuiProjectEditStatus(QWidget):

    def __init__(self, theParent, theStatus):
        QWidget.__init__(self, theParent)

        self.theParent  = theParent
        self.theStatus  = theStatus
        self.colData    = []
        self.colCounts  = []
        self.colChanged = False
        self.selColour  = None

        self.mainBox    = QHBoxLayout()
        self.mainForm   = QVBoxLayout()

        self.listBox    = QListWidget()
        self.listBox.setDragDropMode(QAbstractItemView.InternalMove)
        self.listBox.itemSelectionChanged.connect(self._selectedItem)
        self.listBox.model().rowsMoved.connect(self._rowsMoved)

        for iName, iCol, nUse in self.theStatus:
            self._addItem(iName, iCol, iName, nUse)

        self.editName   = QLineEdit()
        self.newButton  = QPushButton("New")
        self.delButton  = QPushButton("Delete")
        self.saveButton = QPushButton("Save")
        self.colPixmap  = QPixmap(16,16)
        self.colPixmap.fill(QColor(120,120,120))
        self.colButton  = QPushButton(QIcon(self.colPixmap),"Colour")
        self.colButton.setIconSize(self.colPixmap.rect().size())

        self.newButton.clicked.connect(self._newItem)
        self.delButton.clicked.connect(self._delItem)
        self.saveButton.clicked.connect(self._saveItem)
        self.colButton.clicked.connect(self._selectColour)

        self.mainForm.addWidget(self.newButton)
        self.mainForm.addWidget(self.delButton)
        self.mainForm.addStretch(1)
        self.mainForm.addWidget(QLabel("<b>Name</b>"))
        self.mainForm.addWidget(self.editName)
        self.mainForm.addWidget(self.colButton)
        self.mainForm.addStretch(1)
        self.mainForm.addWidget(self.saveButton)

        self.mainBox.addWidget(self.listBox)
        self.mainBox.addLayout(self.mainForm)

        self.setLayout(self.mainBox)

        return

    def getNewList(self):
        if self.colChanged:
            newList = []
            for n in range(self.listBox.count()):
                nItem = self.listBox.item(n)
                nIdx  = nItem.data(Qt.UserRole)
                newList.append(self.colData[nIdx])
            return newList
        return None

    ##
    #  User Actions
    ##

    def _selectColour(self):
        logger.verbose("Item colour button clicked")
        if self.selColour is not None:
            newCol = QColorDialog.getColor(self.selColour, self, "Select Colour", QColorDialog.DontUseNativeDialog)
            if newCol:
                self.selColour = newCol
                colPixmap = QPixmap(16,16)
                colPixmap.fill(newCol)
                self.colButton.setIcon(QIcon(colPixmap))
                self.colButton.setIconSize(colPixmap.rect().size())
        return

    def _newItem(self):
        logger.verbose("New item button clicked")
        newItem = self._addItem("New Item", (0, 0, 0), None, 0)
        newItem.setBackground(QBrush(QColor(0,255,0,80)))
        self.colChanged = True
        return

    def _delItem(self):
        logger.verbose("Delete item button clicked")
        selItem = self._getSelectedItem()
        if selItem is not None:
            iRow   = self.listBox.row(selItem)
            selIdx = selItem.data(Qt.UserRole)
            if self.colCounts[selIdx] == 0:
                self.listBox.takeItem(iRow)
                self.colChanged = True
            else:
                self.theParent.makeAlert("Cannot delete status item that is in use.",nwAlert.ERROR)
        return

    def _saveItem(self):
        logger.verbose("Save item button clicked")
        selItem = self._getSelectedItem()
        iRow    = self.listBox.row(selItem)
        if selItem is not None:
            selIdx = selItem.data(Qt.UserRole)
            self.colData[selIdx] = (
                self.editName.text().strip(),
                self.selColour.red(),
                self.selColour.green(),
                self.selColour.blue(),
                self.colData[selIdx][4]
            )
            selItem.setText("%s [%d]" % (self.colData[selIdx][0], self.colCounts[selIdx]))
            selItem.setIcon(self.colButton.icon())
            self.colChanged = True
        return

    def _addItem(self, iName, iCol, oName, nUse):
        newIcon = QPixmap(16,16)
        newIcon.fill(QColor(*iCol))
        newItem = QListWidgetItem()
        newItem.setText("%s [%d]" % (iName, nUse))
        newItem.setIcon(QIcon(newIcon))
        newItem.setData(Qt.UserRole, len(self.colData))
        self.listBox.addItem(newItem)
        self.colData.append((iName,*iCol,oName))
        self.colCounts.append(nUse)
        return newItem

    def _selectedItem(self):
        logger.verbose("Item selected")
        selItem = self._getSelectedItem()
        if selItem is not None:
            selIdx  = selItem.data(Qt.UserRole)
            selVal  = self.colData[selIdx]
            self.selColour = QColor(selVal[1],selVal[2],selVal[3])
            newIcon = QPixmap(16,16)
            newIcon.fill(self.selColour)
            self.editName.setText(selVal[0])
            self.colButton.setIcon(QIcon(newIcon))
        return

    ##
    #  Internal Functions
    ##

    def _getSelectedItem(self):
        selItem = self.listBox.selectedItems()
        if len(selItem) == 0:
            return None
        if isinstance(selItem[0], QListWidgetItem):
            return selItem[0]
        return None

    def _rowsMoved(self):
        logger.verbose("A drag move event occurred")
        self.colChanged = True
        return

# END Class GuiProjectEditStatus

class GuiProjectEditReplace(QWidget):

    def __init__(self, theParent, theProject):
        QWidget.__init__(self, theParent)

        self.theParent  = theParent
        self.theProject = theProject
        self.arChanged  = False

        self.outerBox   = QVBoxLayout()
        self.bottomBox  = QHBoxLayout()
        self.listBox    = QTreeWidget()
        self.listBox.setHeaderLabels(["Keyword","Replace With"])
        self.listBox.itemSelectionChanged.connect(self._selectedItem)
        self.listBox.setIndentation(0)

        for aKey, aVal in self.theProject.autoReplace.items():
            newItem = QTreeWidgetItem(["<%s>" % aKey, aVal])
            self.listBox.addTopLevelItem(newItem)

        self.editKey    = QLineEdit()
        self.editValue  = QLineEdit()
        self.saveButton = QPushButton(QIcon.fromTheme("document-save"),"")
        self.addButton  = QPushButton(QIcon.fromTheme("list-add"),"")
        self.delButton  = QPushButton(QIcon.fromTheme("list-remove"),"")

        self.saveButton.clicked.connect(self._saveEntry)
        self.addButton.clicked.connect(self._addEntry)
        self.delButton.clicked.connect(self._delEntry)

        self.bottomBox.addWidget(self.editKey, 2)
        self.bottomBox.addWidget(self.editValue, 3)
        self.bottomBox.addWidget(self.saveButton)
        self.bottomBox.addWidget(self.addButton)
        self.bottomBox.addWidget(self.delButton)

        self.outerBox.addWidget(self.listBox)
        self.outerBox.addLayout(self.bottomBox)
        self.setLayout(self.outerBox)

        return

    def getNewList(self):
        newList = {}
        for n in range(self.listBox.topLevelItemCount()):
            tItem = self.listBox.topLevelItem(n)
            aKey  = self._stripNotAllowed(tItem.text(0))
            aVal  = tItem.text(1)
            if len(aKey) > 0:
                newList[aKey] = aVal
        return newList

    ##
    #  Internal Functions
    ##

    def _selectedItem(self):
        selItem = self._getSelectedItem()
        if selItem is None:
            return False
        editKey = self._stripNotAllowed(selItem.text(0))
        editVal = selItem.text(1)
        self.editKey.setText(editKey)
        self.editValue.setText(editVal)
        return True

    def _saveEntry(self):

        selItem = self._getSelectedItem()
        if selItem is None:
            return False

        newKey  = self.editKey.text()
        newVal  = self.editValue.text()
        saveKey = self._stripNotAllowed(newKey)

        if len(saveKey) > 0 and len(newVal) > 0:
            selItem.setText(0,"<%s>" % saveKey)
            selItem.setText(1,newVal)
            self.editKey.clear()
            self.editValue.clear()
            self.arChanged = True

        return

    def _addEntry(self):
        saveKey = "<keyword%d>" % (self.listBox.topLevelItemCount() + 1)
        newVal  = ""
        newItem = QTreeWidgetItem([saveKey, newVal])
        self.listBox.addTopLevelItem(newItem)
        return True

    def _delEntry(self):
        selItem = self._getSelectedItem()
        if selItem is None:
            return False
        self.listBox.takeTopLevelItem(self.listBox.indexOfTopLevelItem(selItem))
        self.arChanged = True
        return True

    def _getSelectedItem(self):
        selItem = self.listBox.selectedItems()
        if len(selItem) == 0:
            return None
        return selItem[0]

    def _stripNotAllowed(self, theKey):
        retKey = ""
        for c in theKey:
            if c.isalnum():
                retKey += c
        return retKey

# END Class GuiProjectEditReplace

# -*- coding: utf-8 -*-
"""novelWriter Error Tester
"""

import nw
import pytest

from PyQt5.QtWidgets import qApp

from dummy import causeException

from nw.error import NWErrorMessage, exceptionHandler

@pytest.mark.base
def testBaseError_Dialog(qtbot, monkeypatch, fncDir, tmpDir):
    """Test the error dialog.
    """
    qApp.closeAllWindows()
    nwGUI = nw.main(["--testmode", "--config=%s" % fncDir, "--data=%s" % tmpDir])
    qtbot.addWidget(nwGUI)
    nwGUI.show()
    qtbot.waitForWindowShown(nwGUI)

    nwErr = NWErrorMessage(nwGUI)
    qtbot.addWidget(nwErr)
    nwErr.show()

    # Invalid Error Message
    nwErr.setMessage(Exception, "Faulty Error", 123)
    assert nwErr.msgBody.toPlainText() == "Failed to generate error report ..."

    # Valid Error Message
    monkeypatch.setattr("PyQt5.QtCore.QSysInfo.kernelVersion", lambda: "1.2.3")
    nwErr.setMessage(Exception, "Fine Error", None)
    theMessage = nwErr.msgBody.toPlainText()
    assert theMessage
    assert "Fine Error" in theMessage
    assert "Exception" in theMessage
    assert "(1.2.3)" in theMessage
    monkeypatch.undo()

    # No kernel version retrieved
    monkeypatch.setattr("PyQt5.QtCore.QSysInfo.kernelVersion", causeException)
    nwErr.setMessage(Exception, "Almost Fine Error", None)
    theMessage = nwErr.msgBody.toPlainText()
    assert theMessage
    assert "(Unknown)" in theMessage
    monkeypatch.undo()

    nwErr._doClose()
    nwErr.close()
    nwGUI.closeMain()

# END Test testBaseError_Dialog

@pytest.mark.base
def testBaseError_Handler(qtbot, monkeypatch, fncDir, tmpDir):
    """Test the error handler. This test doesn'thave any asserts, but it
    checks that the error handler handles potential exceptions. The test
    will fail if excpetions are not handled.
    """
    qApp.closeAllWindows()
    nwGUI = nw.main(["--testmode", "--config=%s" % fncDir, "--data=%s" % tmpDir])
    qtbot.addWidget(nwGUI)
    nwGUI.show()
    qtbot.waitForWindowShown(nwGUI)

    # Normal shutdown
    monkeypatch.setattr(NWErrorMessage, "exec_", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.exit", lambda *args: None)
    exceptionHandler(Exception, "Error Message", None)
    monkeypatch.undo()

    # Should not crash when no GUI is found
    monkeypatch.setattr(NWErrorMessage, "exec_", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.exit", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.topLevelWidgets", lambda: [])
    exceptionHandler(Exception, "Error Message", None)
    monkeypatch.undo()

    # Should handle qApp failing
    monkeypatch.setattr(NWErrorMessage, "exec_", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.exit", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.topLevelWidgets", causeException)
    exceptionHandler(Exception, "Error Message", None)
    monkeypatch.undo()

    # Should handle failing to close main GUI
    monkeypatch.setattr(NWErrorMessage, "exec_", lambda *args: None)
    monkeypatch.setattr("PyQt5.QtWidgets.qApp.exit", lambda *args: None)
    monkeypatch.setattr(nwGUI, "closeMain", causeException)
    exceptionHandler(Exception, "Error Message", None)
    monkeypatch.undo()

    nwGUI.closeMain()

# END Test testBaseError_Handler

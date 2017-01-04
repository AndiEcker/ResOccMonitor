# for single application instance: only needed for python2
import sip
sip.setapi('QString', 2)

import sys, os
import ConfigParser

from PyQt4.Qt import Qt
from PyQt4.QtCore import QSettings, pyqtSlot, QSharedMemory, pyqtSignal, qDebug, QIODevice
from PyQt4.QtGui import QApplication, QMainWindow, QCloseEvent, QStatusBar, \
                        QTableView, QAbstractItemView
from PyQt4.QtNetwork import QLocalServer, QLocalSocket

from app_const import APP_TITLE, APP_VERSION, REFRESH_INTERVAL, PKEY_COL_CNT
from model import CountersModel

class SingleApplication(QApplication):
    messageAvailable = pyqtSignal(object)

    def __init__(self, argv, syncKey):
        #super(SingleApplication, self).__init__(self, argv)
        QApplication.__init__(self, argv)
        self._memory = QSharedMemory(self)
        self._memory.setKey(syncKey)
        if self._memory.attach():
            self._running = True
        else:
            self._running = False
            if not self._memory.create(1):
                raise RuntimeError(self._memory.errorString())

    def isRunning(self):
        return self._running


class SingleApplicationWithMessaging(SingleApplication):
    def __init__(self, argv, syncKey):
        #super(SingleApplicationWithMessaging, self).__init__(self, argv, syncKey)
        SingleApplication.__init__(self, argv, syncKey)
        self._key = syncKey
        self._timeout = 1000
        self._server = QLocalServer(self)
        if not self.isRunning():
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)

    def handleMessage(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(self._timeout):
            self.messageAvailable.emit(
                socket.readAll().data().decode('utf-8'))
            socket.disconnectFromServer()
        else:
            qDebug(socket.errorString())

    def sendMessage(self, message):
        if self.isRunning():
            socket = QLocalSocket(self)
            socket.connectToServer(self._key, QIODevice.WriteOnly)
            if not socket.waitForConnected(self._timeout):
                print(socket.errorString())
                return False
            if not isinstance(message, bytes):
                message = message.encode('utf-8')
            socket.write(message)
            if not socket.waitForBytesWritten(self._timeout):
                print(socket.errorString())
                return False
            socket.disconnectFromServer()
            return True
        return False



class MainWindow(QMainWindow):
    """
        UI Initialization
    """
    def __init__(self, app, config, model, *args):
        QMainWindow.__init__(self, *args)
        #super(MainWindow, self).__init__(self, *args)
        
        self.app = app
        self.config = config        # currently not used for window settings (using QSettings for win pos/size)
        self.countersModel = model
 
        self.countersView = QTableView(self)       # table view with counters
        self.countersView.setModel(self.countersModel)

        self.countersView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.countersView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.countersView.resizeColumnsToContents()

        self.setCentralWidget(self.countersView)
        
        self.setStatusBar(QStatusBar(self))
        
        self.startTimer(REFRESH_INTERVAL)

        
    # main win close events
    # .. (cancel closing with event.ignore(); QMainWindow calls event.accept())       
    @pyqtSlot(QCloseEvent)
    def closeEvent(self, event):
        self._saveAppState()
        # accept window closing
        QMainWindow.closeEvent(self, event)
        # quit application
        self.app.quit()

    """
        Helping methods and slots
    """
    @pyqtSlot(str)
    def handleMessage(self, message):
        print message   # sent by second app instance to pass parameters (to be added to if not yet exists)
        params = message.split()
        nI = PKEY_COL_CNT
        while len(params) >= nI:
            self.countersModel.putRsYrWk(params[nI - PKEY_COL_CNT : nI])
            nI += PKEY_COL_CNT
    
    @pyqtSlot(object)
    def timerEvent(self, evt):
        diffMsg = self.countersModel.refreshFromDb()
        if diffMsg:
            self._displayStatusMsg(diffMsg)
    
    
    def _displayStatusMsg(self, text):
        self.statusBar().showMessage(text)
        
    # main win save/restore
    def _saveAppState(self):
        app.processEvents()
        # save win geometry and splitter positions
        _UI_SAVE(self, 'win_geometry')
    def _restoreAppState(self):
        try:    # will fail on first app startup after installation
            # restore last win position, -size and 3 splitter positions
            _UI_RESTORE(self, 'win_geometry')
        except: # first start
            screenWidth = QApplication.desktop().width()
            screenHeight = QApplication.desktop().height()
            self.setGeometry(0, 0, screenWidth / 2.7, screenHeight / 1.56)


# global settings repository and helping functions
m_settings = QSettings('User', 'ResOccMonitor')
def _UI_SAVE(widget, key):
    if key[:4] == 'win_':
        m_settings.setValue(key, widget.saveGeometry())
    else:
        m_settings.setValue(key, widget.saveState())
def _UI_RESTORE(widget, key):
    if key[:4] == 'win_':
        # win size not fully restored if too small for displayed content?!?!?
        widget.restoreGeometry(m_settings.value(key).toByteArray())
    else:
        widget.restoreState(m_settings.value(key).toByteArray())


if __name__ == '__main__':
    args = sys.argv

    syncKey = 'ResOccMonitorSyncKey'

    app = SingleApplicationWithMessaging(args, syncKey)
    if app.isRunning():
        print(args[0] + ' is already running')
        # forward/send command line arguments as message
        app.sendMessage(' '.join(args[1:]))
        sys.exit(1)

    # have to change explicitly to the EXE folder because Omnis is not changing the working directory
    # .. and we cannot use app.applicationDirPath() because it is returning C:\Python27 within Eclipse
    exePath = os.path.dirname(args[0])
    # .. we also could change the current working directory to the installation directory with: QDir.setcurrent(exePath)
    cfgFile = exePath + '/ResOccMonitor.cfg'
    print os.getcwd()
    config = ConfigParser.SafeConfigParser()
    try:
        config.readfp(open(cfgFile))
    except:
        print 'config file ' + cfgFile + ' not found!'
        config = None
    
    # initialize data model
    model = CountersModel(config, app)
    nI = 3
    while len(args) - 1 >= nI:
        model.putRsYrWk(args[nI - 2:nI + 1])
        nI += 3    

    win = MainWindow(app, config, model)
    app.messageAvailable.connect(win.handleMessage)

    win.setWindowTitle(APP_TITLE + " " + APP_VERSION + " on " + config.get("main", "DbConnect").split('@')[1])
    win.setWindowFlags(Qt.WindowStaysOnTopHint)
    win.show()
    win._restoreAppState()
    
    sys.exit(app.exec_())

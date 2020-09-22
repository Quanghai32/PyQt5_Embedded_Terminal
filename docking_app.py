import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import gi
import uuid
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk
import time

class Container(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)
        self.embed()

    def embed(self):
        self.name_session = uuid.uuid4().hex
        proc = QtCore.QProcess()

        started, procId = QtCore.QProcess.startDetached(
            "xterm", ["-e", "tmux", "new", "-s", self.name_session], "."
        )
        if not started:
            QtWidgets.QMessageBox.critical(self, 'Process not started', "Eh")
            return
        attempts = 0
        while attempts < 10:
            screen = Wnck.Screen.get_default()
            screen.force_update()
            # do a bit of sleep, else window is not really found
            time.sleep(0.1)
            # this is required to ensure that newly mapped window get listed.
            while Gdk.events_pending():
                Gdk.event_get()
            for w in screen.get_windows():
                print(attempts, w.get_pid(), procId, w.get_pid() == procId)
                if w.get_pid() == procId:
                    self.window = QtGui.QWindow.fromWinId(w.get_xid())
                    proc.setParent(self)
                    win32w = QtGui.QWindow.fromWinId(w.get_xid())
                    win32w.setFlags(QtCore.Qt.FramelessWindowHint)
                    widg = QtWidgets.QWidget.createWindowContainer(win32w)

                    self.addTab(widg, 'abc')
                    self.resize(500, 400) # set initial size of window
                    return
            attempts += 1
        QtWidgets.QMessageBox.critical(self, 'Window not found', 'Process started but window not found')

    def stop(self):
        QtCore.QProcess.execute("tmux", ["kill-session", "-t", self.name_session])

    def send_command(self, command):
        QtCore.QProcess.execute(
            "tmux", ["send-keys", "-t", self.name_session, command, "Enter"]
        )

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.ifconfig_btn = QtWidgets.QPushButton("ifconfig")
        self.ping_btn = QtWidgets.QPushButton("ping")
        self.terminal = Container()

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        lay = QtWidgets.QGridLayout(central_widget)
        lay.addWidget(self.ifconfig_btn, 0, 0)
        lay.addWidget(self.ping_btn, 0, 1)
        lay.addWidget(self.terminal, 1, 0, 1, 2)

        self.resize(640, 480)

        self.ifconfig_btn.clicked.connect(self.launch_ifconfig)
        self.ping_btn.clicked.connect(self.launch_ping)

    def launch_ifconfig(self):
        self.terminal.send_command("ifconfig")

    def launch_ping(self):
        self.terminal.send_command("ping 8.8.8.8")

    def closeEvent(self, event):
        self.terminal.stop()
        super().closeEvent(event)

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())
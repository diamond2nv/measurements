# Cavity GUI client for QTLab, adapted from Cyclops client for QTlab
# 
# Author: Wolfgang Pfaff <w.pfaff@tudelft.nl>, adapted by Suzanne van Dam

### Stuff we need to get cavity gui up and running
import logging
l = logging.getLogger()
l.setLevel(logging.WARNING)

# make sure the userconfig is loaded
import os, sys
os.environ['ETS_TOOLKIT'] = 'qt4'
execfile('userconfig.py')

# we need this for ETS to work properly with pyqt
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)
from PyQt4 import QtGui, QtCore


import time
import socket
import gobject
from lib.network.object_sharer import helper
from lib.network.tcpserver import GlibTCPHandler
PORT = 12002

### some useful things that might get imported by other scripts
CONFIG_FILE = os.path.join(os.getcwd(), 'userconfig.py')

# methods/classes for QT4 clients that replace the glib-based ones
class QtTCPHandler(GlibTCPHandler, QtCore.QObject):
    def __init__(self, sock, client_address, server, packet_len=False):
        QtCore.QObject.__init__(self)
        GlibTCPHandler.__init__(self, sock, client_address, server, packet_len)

        self.socket_notifier = QtCore.QSocketNotifier(\
            self.socket.fileno(), QtCore.QSocketNotifier.Read)
        self.socket_notifier.setEnabled(True)
        self.socket_notifier.activated.connect(self._socketwatcher_recv)
        
    def enable_callbacks(self):
        return

    def disable_callbacks(self):
        return

    # @QtCore.pyqtSlot()
    def _socketwatcher_recv(self, *args):
        self._handle_recv(self.socket, gobject.IO_IN)

# class QtTCPHandler
class _QtDummyHandler(QtTCPHandler):
    def __init__(self, sock, client_address, server):
        QtTCPHandler.__init__(self, sock, client_address, server,
                packet_len=True)
        helper.add_client(self.socket, self)

    def handle(self, data):
        if len(data) > 0:
            data = helper.handle_data(self.socket, data)
        return True

# class _QtDummyHandler

# here we go...
if __name__ == "__main__":
    
    # default config
    from cavity_gui import config

    # load user config
    if os.path.exists(CONFIG_FILE):
        execfile(CONFIG_FILE)


    # start our first application
    from main_window import MainWindow

    # not using styles atm, at some point later...
    #style = open(os.path.join(os.getcwd(),
    #                          'source/gui/cyclops/style.css'), 'r').read()
    cavity_gui_app = QtGui.QApplication(sys.argv)
    # cyclops_app.setStyleSheet(style)

    # open the socket and start the client.
    # will fail if no connection to qtlab is available   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', PORT))    
    handler = _QtDummyHandler(sock, 'client', 'server')
    
    mainwindow = MainWindow()
    mainwindow.show()
    
    sys.exit(cavity_gui.exec_())


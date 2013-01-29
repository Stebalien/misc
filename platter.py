#!/usr/bin/python2

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import os, urllib, socket, sys,base64
import qrcode
from PyQt4 import QtGui, QtCore
import ImageQt

BUF_SIZE = 16*1024

nop = lambda *_:None

def make_code(length=6):
    return base64.urlsafe_b64encode(os.urandom(length))

def async(func):
    def do(*args, **kwargs):
        if "callback" in kwargs:
            cb = kwargs.pop("callback")
            thread = threading.Thread(target=lambda: cb(func(*args, **kwargs)))
        else:
            thread = threading.Thread(target=lambda: func(*args, **kwargs))
        thread.start()
        return thread
    return do


def find_ip ():
   # we get a UDP-socket for the TEST-networks reserved by IANA.
   # It is highly unlikely, that there is special routing used
   # for these networks, hence the socket later should give us
   # the ip address of the default route.
   # We're doing multiple tests, to guard against the computer being
   # part of a test installation.

   try:
       candidates = []
       for test_ip in ["192.0.2.0", "198.51.100.0", "203.0.113.0"]:
           s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
           s.connect ((test_ip, 80))
           ip_addr = s.getsockname ()[0]
           s.close ()
           if ip_addr in candidates:
               return ip_addr
       candidates.append(ip_addr)
       return candidates[0]
   except socket.error as e:
       if e.errno == 101:
           return "127.0.0.1"
       else:
           raise e


class SingleFileHTTPRequestHandler(BaseHTTPRequestHandler):
    canceled = False
    def do_GET(self):
        if self.path != self.server.path:
            self.send_error(404)
            return

        try:
            filename = self.server.filename
            fsize = self.server.fsize
            self.server.trigger("start", self)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment;filename=%s" % urllib.quote(os.path.basename(filename)))
            self.send_header('Content-Length', fsize)
            self.end_headers()

            percent_increment = float(BUF_SIZE)/float(fsize)*100
            percent_complete = 0

            with open(filename) as fobj:
                while True:
                    buf = fobj.read(BUF_SIZE)
                    if not buf:
                        break
                    if self.canceled:
                        return
                    self.wfile.write(buf)
                    percent_complete += percent_increment
                    self.server.trigger("progress", self, percent_complete)
        except:
            self.server.trigger("failure", self)
        else:
            self.server.trigger("success", self)

    def cancel(self):
        self.canceled = True
        if not self.wfile.closed:
            try:
                self.wfile.close()
            except:
                pass
        if not self.rfile.closed:
            try:
                self.rfile.close()
            except:
                pass

class SingleFileHTTPServer(ThreadingMixIn, HTTPServer):
    callbacks = {}
    def __init__(self, filename, address=("", 0), handler=SingleFileHTTPRequestHandler, **kwargs):
        HTTPServer.__init__(self, address, handler, **kwargs)
        self.filename = filename
        self.path = "/" + make_code()
        self.fsize = os.path.getsize(filename)
        self.url = "http://%s:%d%s" % (find_ip(), self.server_port, self.path)

    def trigger(self, signal, *args, **kwargs):
        for cb in self.callbacks.get(signal, ()):
            cb(*args, **kwargs)
        for cb in self.callbacks.get("all", ()):
            cb(signal, *args, **kwargs)

    def on(self, signal, cb):
        self.callbacks.setdefault(signal, set()).add(cb)

    def off(self, signal, cb):
        if signal in self.callbacks:
            self.callbacks[signal].remove(cb)

class Platter(QtGui.QApplication):
    def __init__(self, args):
        super(Platter, self).__init__(args)
        self.transfers = {}

        self.server = SingleFileHTTPServer(args[1])
        self.main = PlatterUI()

        self.connectSignals()

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def connectSignals(self):
        self.server.on("progress", self.proxyProgress)
        self.server.on("failure", self.proxyFailure)
        self.server.on("success", self.proxySuccess)
        self.server.on("start", self.proxyStart)
        self.aboutToQuit.connect(self.onQuit)

    def onQuit(self):
        self._shutdown()

    def _shutdown(self):
        self.server.shutdown()
        self.server_thread.join()

    @async
    def shutdown(self):
        self._shutdown()
        self.quit()

    def proxyStart(self, transfer):
        self.main.addTransferSignal.emit(transfer)

    def proxyProgress(self, transfer, progress):
        try:
            pane = self.transfers[transfer.client_address[0]]
        except KeyError:
            return
        pane.progressSignal.emit(progress)

    def proxySuccess(self, transfer):
        try:
            pane = self.transfers[transfer.client_address[0]]
        except KeyError:
            return
        pane.successSignal.emit()

    def proxyFailure(self, transfer):
        try:
            pane = self.transfers[transfer.client_address[0]]
        except KeyError:
            return
        pane.failureSignal.emit()

class PlatterUI(QtGui.QWidget):
    addTransferSignal = QtCore.pyqtSignal(object)
    quitSignal = QtCore.pyqtSignal()

    def __init__(self):
        super(PlatterUI, self).__init__()
        self.app = QtGui.QApplication.instance()
        QtGui.QIcon.setThemeName('Faenza')

        self.initUI()
        self.connectSignals()

    def connectSignals(self):
        self.addTransferSignal.connect(self.onAddTransfer, QtCore.Qt.BlockingQueuedConnection)
        #self.quitSignal.connect(self.onQuit)

    def initUI(self):
        #self.setGeometry(300, 300, 250, 150)
        self.setWindowFlags(QtCore.Qt.Dialog)
        frame = self.frameGeometry()
        frame.moveCenter(self.app.desktop().availableGeometry().center())
        self.move(frame.topLeft())

        
        # Build pane
        self.content = QtGui.QWidget()
        content_layout = QtGui.QHBoxLayout()
        content_layout.addLayout(self.makeQRCode())
        content_layout.addLayout(self.makeInfoPane())
        content_layout.addStretch(1)
        content_layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.content.setLayout(content_layout)

        window_layout = QtGui.QHBoxLayout(self)
        window_layout.addWidget(self.content)

        self.setLayout(window_layout)
        self.setWindowTitle('Platter')
        self.show()

    def makeQRCode(self):
        image = qrcode.make(self.app.server.url, box_size=5)
        pixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(image))
        label = QtGui.QLabel('', self)
        label.setPixmap(pixmap)
        container = QtGui.QVBoxLayout()
        container.addWidget(label)
        container.addStretch(1)
        return container

    def makeInfoPane(self):
        title = QtGui.QLabel('<font face="Droid Sans"><h1>{filename}</h1></font>'.format(
            filename=os.path.basename(self.app.server.filename),
        ))

        pane = QtGui.QVBoxLayout()
        pane.addWidget(title)
        pane.addLayout(self.makeUrlPane())
        pane.addWidget(self.makeTransferPane())
        return pane

    def makeUrlPane(self):
        url = QtGui.QLabel(self.app.server.url)
        copyLink = QtGui.QToolButton()
        copyLink.setText('Copy')
        copyLink.setIcon(QtGui.QIcon.fromTheme("edit-copy"))
        copyLink.clicked.connect(self.copyToClipboard)

        url_pane = QtGui.QHBoxLayout()
        url_pane.addWidget(url)
        url_pane.addWidget(copyLink)
        url_pane.addStretch(1)
        return url_pane

    def makeTransferPane(self):
        transfer_container = QtGui.QWidget()
        self.transfer_pane = QtGui.QVBoxLayout()
        self.transfer_pane.setSpacing(0)
        self.transfer_pane.setMargin(0)
        self.transfer_pane.addStretch(1)

        outer_layout = QtGui.QVBoxLayout()
        outer_layout.addLayout(self.transfer_pane)
        outer_layout.addStretch(1)
        transfer_container.setLayout(outer_layout)

        scroll_container = QtGui.QScrollArea()
        scroll_container.setWidget(transfer_container)
        scroll_container.setWidgetResizable(True)
        return scroll_container

    def copyToClipboard(self):
        self.app.clipboard().setText(self.app.server.url)

    def onAddTransfer(self, request):
        address = str(request.client_address[0])
        # Assume that devices only download once (to work around chromes double get)
        if address in self.app.transfers:
            transfer = self.app.transfers[address]
        else:
            transfer = TransferPane(address)
            self.app.transfers[address] = transfer
            self.transfer_pane.addWidget(transfer)
        transfer.addRequest(request)
        transfer.onStart()

    def insertTrans(self, widget):
        self.transfer_pane.addWidget(widget)

    def closeEvent(self, e):
        self.app.shutdown()
        e.ignore()
        self.layout().takeAt(0).widget().hide()
        label = QtGui.QLabel("Shutting down...")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(label)


    def keyPressEvent(self, e):
        if e.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Q):
            self.close()

class TransferPane(QtGui.QWidget):
    progressSignal = QtCore.pyqtSignal(int)
    successSignal = QtCore.pyqtSignal()
    failureSignal = QtCore.pyqtSignal()
    def __init__(self, address):
        super(TransferPane, self).__init__()
        self.app = QtGui.QApplication.instance()
        self.address = address
        self.requests = []

        self.initUI()
        self.connectSignals()

    def initUI(self):
        self.progress_bar = QtGui.QProgressBar()

        self.close_button = QtGui.QToolButton()
        self.close_button.setIcon(QtGui.QIcon.fromTheme("window-close"))
        self.close_button.clicked.connect(self.remove)


        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

    def connectSignals(self):
        self.progressSignal.connect(self.onProgress)
        self.successSignal.connect(self.onSucceed)
        self.failureSignal.connect(self.onFailure)

    def onProgress(self, progress):
        self.progressbar.setValue(progress)

    def onStart(self):
        self.progress_bar.setFormat("{address} - %p%".format(address=self.address))
        self.progress_bar.setValue(0)

    def addRequest(self, request):
        self.requests.append(request)

    def onSucceed(self):
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("{address} - Completed".format(address=self.address))

    def onFailure(self):
        self.progress_bar.setFormat("{address} - Failed".format(address=self.address))
    
    def remove(self):
        for request in self.requests:
            request.cancel()

        self.app.main.transfer_pane.removeWidget(self)
        del self.app.transfers[self.address]
        v = self.layout().takeAt(0)
        while v:
            v.widget().hide()
            v = self.layout().takeAt(0)


if __name__ == "__main__":
    app = Platter(sys.argv)
    sys.exit(app.exec_())

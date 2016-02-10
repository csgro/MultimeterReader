#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
from PyQt4 import QtCore, QtGui
import time
import logging as myLogger
myLogger.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                   level=myLogger.INFO)

import visa

class Multimeter:
    def __init__(self):        
        #print "here connection with multimeter"
        self.rm = visa.ResourceManager()
        #myLogger.debug("Listing VISA resources: %s" % self.rm.list_resources())
	print(self.rm.list_resources())
	
        # A USB Test & Measurement class device with 
	# manufacturer ID 0x0957, model code 0xB318, and serial number MY55060040. 
	self.my_inst = self.rm.open_resource('USB0::0x0957::0xB318::MY55060040::INSTR')
	# init instrument
	self.my_inst.write('*RST')
		
	# print instrument info:
	myLogger.info("Instrument info: %s " % self.my_inst.query('*IDN?'))
		
	self.configDC()
		
    def configDC(self, MaxV=100, Res = 3.0e-5):
	my_str = 'CONF:VOLT:DC %d,%.1e' % (MaxV, Res)
	myLogger.info("Instrument DCV config: %s " % my_str)
	self.my_inst.write(my_str)
	self.my_inst.write('TRIG:SOUR IMM')	

    def readVolt(self):
        t0 = time.time()
        v0 = self.my_inst.query("READ?")
        t1 = time.time() # average before and after to get better time
        v0 = float(v0)
        return (0.5*(t0+t1),v0)

    
class MultimeterDummy:
    """Dummy class for standalone test
    """
    def __init__(self):
        # print instrument info:
        from random import randint
        self.myRandom = randint
	myLogger.info("Instrument info: Dummy")


    def configDC(self, MaxV=100, Res = 3.0e-5):
        pass

    def readVolt(self):
        t0 = time.time()
        v0 = self.myRandom(1,10)
        return (t0,v0)
    
class gMainWindow(QtGui.QMainWindow):
    """ Simple gui for Multimeter readout.
    Just buttons (Start/Stop, Quit).
    Readout synch  with QTimer timeout with selectable time interval
    TODO: add write file complete path
    """

    READOUT_INTERVALS = {"10 ms": 10, "100 ms": 100, "500 ms": 500, "1 s": 1000, "10 s": 10000}

    
    def __init__(self):
        super(gMainWindow, self).__init__()
        self.setupUI()
        self.Running = False
        self.setupRadout()

    def setupRadout(self):
        #self.multimeter = Multimeter()
        self.multimeter = MultimeterDummy()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateValue)
        self.FirstTime = None
        
    def updateValue(self):
        Values = self.multimeter.readVolt()
        if self.FirstTime == None:
            self.FirstTime = Values[0]
        if self.ofname != None:
            ff = open(self.ofname, 'a')
            ff.write("%f\t%f\n"%(Values[0]-self.FirstTime, Values[1]))
        self.statusBar().showMessage("T= %f V = %f" % \
                                     (Values[0]-self.FirstTime, Values[1]))
        myLogger.info("reading %f:%f" %(Values[0]-self.FirstTime, Values[1]))
        
    def setupUI(self):
        self.setGeometry(100, 100, 250, 200)
        self.setWindowTitle('Voltage Reader')

        # buttons setup
        self.btnStartStop = QtGui.QPushButton('START', self)
        self.btnStartStop.setFixedSize(90, 55)
        self.btnStartStop.move(10, 120)
        self.btnStartStop.clicked.connect(self.ToggleDaq)
        self.btnStartStop.setFont(QtGui.QFont('SansSerif', 12))
        
        #btnStart = QtGui.QPushButton('START', self)
        #btnStart.setFixedSize(70, 55)
        #btnStart.move(90, 120)
        #btnStart.clicked.connect(self.StartDaq)

        #btnStop = QtGui.QPushButton('STOP', self)
        #btnStop.setFixedSize(70, 55)
        #btnStop.move(10, 120)
        #btnStop.clicked.connect(self.StopDaq)
        
        btnQuit = QtGui.QPushButton('Quit', self)
        btnQuit.setFixedSize(70, 55)
        btnQuit.move(170, 120) #190, 120)
        btnQuit.clicked.connect(self.CloseAll)

        # out file line edit
        lbOutFile = QtGui.QLabel(self)
        lbOutFile.move(10,2)
        lbOutFile.setText('Output File Name')
        lbOutFile.adjustSize() 
        self.leOutFile = QtGui.QLineEdit(self)
        self.leOutFile.resize(230, 30)
        self.leOutFile.move(10, 20)

        # redout time
        rlInterval = QtGui.QLabel(self)
        rlInterval.move(10,68)
        rlInterval.setText('Readout interval')
        rlInterval.adjustSize() 
        self.rcInterval = QtGui.QComboBox(self)
        self.rcInterval.move(140,60)
        for ss in self.READOUT_INTERVALS.keys():
            self.rcInterval.addItem(ss)
        
        # enable status bar
        self.statusBar().showMessage('Ready')

    def CloseAll(self):
        # stop acquisition if necessary and quit
        if self.Running:
            self.StopDaq()
        myLogger.info("bye!")
        QtCore.QCoreApplication.instance().quit()

    def ToggleDaq(self):
        if not self.Running:
            self.StartDaq()
            self.btnStartStop.setText('STOP')
        else:
            self.StopDaq()
            self.btnStartStop.setText('START')
            
    def StartDaq(self):
        # check output file
        self.ofname = self.leOutFile.text()
        if self.ofname == "":
            myLogger.warning("No output file selected")
            self.ofname = None
        else:
            if os.path.exists(self.ofname):
                myLogger.warning("File %s already exists! Adding _1 to it!" %\
                               self.ofname)
                self.ofname += "_1"
                self.leOutFile.setText(self.ofname)
            myLogger.info("Writing output file %s" % self.ofname)
            ff = open(self.ofname, 'a')
            ff.write("#Time [s]\tDCV [V]\n")
        self.leOutFile.setEnabled(False)

        # check readout interval:
        txt = self.rcInterval.currentText()
        roTime = self.READOUT_INTERVALS[str(txt)]
        self.rcInterval.setEnabled(False)
        if not self.Running:
            self.timer.start(roTime)
            self.statusBar().showMessage('Started')
            myLogger.info("Acquisition started")
            self.Running = True
        else:
            pass
        
    def StopDaq(self):
        self.leOutFile.setEnabled(True)
        self.rcInterval.setEnabled(True)
        if self.Running:
            self.timer.stop()
            self.statusBar().showMessage('Stopped')
            myLogger.info("Acquisition stopped")
            self.Running = False
        else:
            pass

        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    vm  = gMainWindow()
    vm.show()
    sys.exit(app.exec_())

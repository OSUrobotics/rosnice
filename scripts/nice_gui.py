#!/usr/bin/env python
import roslib; roslib.load_manifest('rosnice')
import rosnode
import rospy
import xmlrpclib
import psutil
from collections import namedtuple

import sys
from PySide import QtGui, QtCore

# InfoWidget = namedtuple('InfoWidget', 'widget to_str')

ID = '/NICEGUI'

class InfoWidget(object):
	widget = None
	to_str = None
	
	def __init__(self, widget, to_str):
		self.widget = widget
		self.to_str = to_str

class ProcessInfoDisplay(QtGui.QWidget):
	# function name | widget | retval -> string
	live_info = {
		'get_nice':			InfoWidget(None, lambda x: str(x)),
		'pid':				InfoWidget(None, lambda x: str(x)),
		'get_cpu_percent':	InfoWidget(None, lambda x: '%s%%' % x),
		'get_memory_info':	InfoWidget(None, lambda x: '\n  (real) %0.2fMiB,\n  (virtual) %0.2fMiB' % (x.rss/2.0**20, x.vms/2.0**20)),
	}
	
	def __init__(self, node_name):
		super(ProcessInfoDisplay, self).__init__()
		self.node_name = node_name
		self.node_api = rosnode.get_api_uri(rospy.get_master(), node_name)
		code, msg, self.pid = xmlrpclib.ServerProxy(self.node_api[2]).getPid(ID)
		try:
			self.process = psutil.Process(self.pid)
		except:
			print 'Bad PID: %s, name: %s, code: %s, msg: %s' % (self.pid, self.node_name, code, msg)
		self.initUI()
		self.timer = QtCore.QTimer(self.parent())
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.update_live_info)
		self.timer.start()
		
	def make_name(self, name):
		pre = 'get_'
		if pre in name:
			return name[name.index('get_') + len(pre):]
		return name
		
	def initUI(self):
		layout = QtGui.QVBoxLayout()
		layout.setDirection(QtGui.QVBoxLayout.Direction.TopToBottom)
		
		self.setLayout(layout)
		
		self.nice_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
		nice = self.process.get_nice()
		self.nice_slider.setValue(nice)
		layout.addWidget(self.nice_slider)
		self.nice_slider.connect(self.nice_slider, QtCore.SIGNAL('valueChanged(int)'), self.sliderChanged)
		
		for func, info in self.live_info.iteritems():
			info.widget = QtGui.QLabel()
			self.layout().addWidget(info.widget)
		
		self.update_live_info()
		
	def sliderChanged(self, val):
		self.process.set_nice(val)
		
	def update_live_info(self):
		self.nice_slider.setValue(self.process.get_nice())
		for func, info in self.live_info.iteritems():
			data = self.process.__getattribute__(func)
			if func.startswith('get'):
				data = data.__call__()
			text = '%s: %s' % (self.make_name(func), info.to_str(data))
			info.widget.setText(text)
			
	def __del__(self):
		self.setParent(None)
		self.timer.disconnect(self.parent())
		del self
		# self.parent().repaint()
			
		
class NodeListWidget(QtGui.QComboBox):
	def __init__(self, parent_layout=None, parent=None):
		super(NodeListWidget, self).__init__(parent)
		self.parent_layout = parent_layout
		self.activated.connect(self.onActivated)
		self.current_info = None
		self.update()
		
	def onActivated(self, index):
		info_widget = ProcessInfoDisplay(self.itemText(index))
		print 'New Widget', info_widget
		if self.current_info is not None:
			self.parent_layout.removeWidget(self.current_info)
			del self.current_info
			
		self.parent_layout.parent().repaint()
		self.parent_layout.parent().repaint()
		self.parent_layout.parent().repaint()
		self.parent_layout.parent().repaint()
		self.parent_layout.parent().repaint()
		self.parent_layout.addWidget(info_widget)
		self.current_info = info_widget
		print self.parent_layout.children()
		
	def resizeEvent(self, e):
		super(NodeListWidget, self).resizeEvent(e)
		
	def paintEvent(self, e):
		super(NodeListWidget, self).paintEvent(e)
		
	def update(self):
		self.addItems(rosnode.get_node_names())
		
class NiceGUI(QtGui.QWidget):
	def __init__(self):
		super(NiceGUI, self).__init__()
		self.initUI()
		self.show()
		
	def initUI(self):
		self.setWindowTitle('rosnice')
		layout = QtGui.QVBoxLayout()
		layout.setDirection(QtGui.QVBoxLayout.Direction.TopToBottom)
		
		self.setLayout(layout)
		node_combo = NodeListWidget(parent_layout=layout)
		self.layout().addWidget(node_combo)
		# node_combo.onActivated(0)
		layout.addStretch(-1)

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	nice_gui = NiceGUI()
	nice_gui.resize(250,150)
	sys.exit(app.exec_())
#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
import time
import urllib.request

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebChannel import QWebChannel

__Author__ = '''wenye'''


class CallHandler(QObject):

    def __init__(self):
        super(CallHandler, self).__init__()

    @pyqtSlot(str, result=str)  # 第一个参数即为回调时携带的参数类型
    def init_home(self, str_args):
        print(str_args)  # 查看参数
        # #####
        # 这里写对应的处理逻辑比如：
        msg = '收到来自python的消息'
        view.page().runJavaScript("alert('%s')" % msg)
        return 'eee'


class WebEngine(QWebEngineView):
    def __init__(self):
        super(WebEngine, self).__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 设置右键菜单规则为自定义右键菜单


    def closeEvent(self, evt):
        self.page().profile().clearHttpCache()  # 清除QWebEngineView的缓存
        super(WebEngine, self).closeEvent(evt)


if __name__ == '__main__':
    # 加载程序主窗口
    app = QApplication(sys.argv)
    view = WebEngine()
    view.setFixedSize(700,400)
    channel = QWebChannel()
    handler = CallHandler()  # 实例化QWebChannel的前端处理对象
    channel.registerObject('PyHandler', handler)  # 将前端处理对象在前端页面中注册为名PyHandler对象，此对象在前端访问时名称即为PyHandler'
    view.page().setWebChannel(channel)
    view.load(
        QUrl(QFileInfo("./index.html").absoluteFilePath()))
    view.show()
    sys.exit(app.exec_())

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
        print('call received')
        print('resolving......init home..')
        print(str_args)  # 查看参数
        # #####
        # 这里写对应的处理逻辑比如：
        msg = '收到来自python的消息'
        view.page().runJavaScript("alert('%s')" % msg)
        view.page().runJavaScript("window.say_hello('%s')" % msg)
        return 'hello, Python'


class WebEngine(QWebEngineView):
    def __init__(self):
        super(WebEngine, self).__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 设置右键菜单规则为自定义右键菜单
        # self.customContextMenuRequested.connect(self.showRightMenu)  # 这里加载并显示自定义右键菜单，我们重点不在这里略去了详细带吗

        self.setWindowTitle('QWebChannel与前端交互')
        self.resize(1100, 650)

    def closeEvent(self, evt):
        self.page().profile().clearHttpCache()  # 清除QWebEngineView的缓存
        super(WebEngine, self).closeEvent(evt)


if __name__ == '__main__':
    # 加载程序主窗口
    app = QApplication(sys.argv)
    view = WebEngine()
    channel = QWebChannel()
    handler = CallHandler()  # 实例化QWebChannel的前端处理对象
    channel.registerObject('PyHandler', handler)  # 将前端处理对象在前端页面中注册为名PyHandler对象，此对象在前端访问时名称即为PyHandler'
    view.page().setWebChannel(channel)  # 挂载前端处理对象
    url_string = urllib.request.pathname2url(os.path.join(os.getcwd(), "index.html"))  # 加载本地html文件
    # 当然您可以加载互联网行的url，也可自行监听本地端口，然后加载本地端口服务的资源，后面有介绍嘻嘻
    # url_string = 'localhost:64291'   # 加载本地html文件
    # print(url_string, '\n', os.path.join(os.getcwd(), "index.html"))
    view.load(
        QUrl(QFileInfo("./index.html").absoluteFilePath()))
    time.sleep(2)
    view.show()
    sys.exit(app.exec_())

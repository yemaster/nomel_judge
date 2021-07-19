#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
import time
import urllib.request
import json

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebChannel import QWebChannel

Contest_Data = {
    "name": "新建比赛",
    "dir": "",
    "problems": [],
    "sources": []
}

class CallHandler(QObject):

    def __init__(self):
        super(CallHandler, self).__init__()

    @pyqtSlot(str, result=str)
    def save_file(self, dict_args):
        global Contest_Data
        try:
            Contest_Data = json.loads(dict_args)
            saveFile = Contest_Data["dir"]
            with open(saveFile, 'w', encoding="utf8") as f:
                f.write(json.dumps(Contest_Data, sort_keys=True, indent=4, separators=(',', ':')))
        except Exception as e:
            print(e)
            view.page().runJavaScript("swal('出错了', '保存失败', 'error')")
        else:
            view.page().runJavaScript("swal('成功', '保存成功', 'success')")
    @pyqtSlot(str, result=str)
    def init_home(self, str_args):
        global Contest_Data
        print(str_args)
        if (str_args == 'New Contest'):
            saveFile = QFileDialog.getSaveFileName(view,
            "保存比赛文件",
            os.getcwd(),
            "JSON Files (*.json)")
            try:
                saveFile = saveFile[0]
                if len(saveFile) == 0:
                    return 'breaked'
                Contest_Data["dir"] = saveFile
                with open(saveFile, 'w', encoding="utf8") as f:
                    f.write(json.dumps(Contest_Data, sort_keys=True, indent=4, separators=(',', ':')))
            except Exception as e:
                print(e)
                view.page().runJavaScript("swal('出错了', '文件不能保存', 'error')")
            else:
                view.page().runJavaScript("nomel_main.InitContest({})".format(Contest_Data))
        elif (str_args == 'Open Contest'):
            saveFile = QFileDialog.getOpenFileName(view,
            "打开比赛文件",
            os.getcwd(),
            "JSON Files (*.json)")
            try:
                saveFile = saveFile[0]
                if len(saveFile) == 0:
                    return 'breaked'
                with open(saveFile, 'r', encoding="utf8") as f:
                    Contest_Data = json.load(f)
                if (not "name" in Contest_Data):
                    raise IOError("文件格式错误")
                if (not "problems" in Contest_Data):
                    Contest_Data["problems"] = []
                if (not "sources" in Contest_Data):
                    Contest_Data["sources"] = []
                Contest_Data["dir"] = saveFile
            except Exception as e:
                print(e)
                view.page().runJavaScript("swal('出错了', '文件读取失败', 'error')")
            else:
                view.page().runJavaScript("nomel_main.InitContest({})".format(Contest_Data))
        #msg = 'asd'
        #view.page().runJavaScript("alert('%s')" % msg)
        return 'OK'


class WebEngine(QWebEngineView):
    def __init__(self):
        super(WebEngine, self).__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)


    def closeEvent(self, evt):
        self.page().profile().clearHttpCache()
        super(WebEngine, self).closeEvent(evt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = WebEngine()
    view.setMinimumSize(720, 480)
    channel = QWebChannel()
    handler = CallHandler()
    channel.registerObject('PyHandler', handler)
    view.page().setWebChannel(channel)
    view.load(
        QUrl(QFileInfo("./index.html").absoluteFilePath()))
    view.show()
    sys.exit(app.exec_())

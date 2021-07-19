#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
import time
import urllib.request
import json
import shutil
import subprocess
import random
import threading

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

Settings = {}
with open('config.json', 'r') as fp:
    Settings = json.load(fp)

def run_code(jm):
    global Contest_Data
    global Settings
    view.page().runJavaScript("nomel_main.isJudge = 1")
    dataDir = Contest_Data["dir"].replace("/", "\\").split("\\")[::-1]
    dataDir.pop(0)
    dataDir = '\\'.join(dataDir[::-1])
    det_s = []
    for ia in range(0, len(Contest_Data["problems"])):
        det_s.append({
            "score": "未评测"
        })
    judged_res = []
    if (jm == 'all'):
        for scs in Contest_Data["sources"]:
            scs["score"] = 0
            scs["used_time"] = 0
            tot = 0
            t = det_s
            for pbs in Contest_Data["problems"]:
                t[tot]["score"] = 0
                langmod = -1
                preFile = dataDir + "\\source\\" + scs["name"] + "\\" + pbs["source_name"]
                print(preFile)
                if os.path.isfile(preFile + ".cpp"):
                    langmod = 0
                    preFile += ".cpp"
                elif os.path.isfile(preFile + ".c"):
                    langmod = 1
                    preFile += ".c"
                if langmod == -1:
                    t[tot]["res"] = "找不到程序"
                    t[tot]["score"] = 0
                    t[tot]["info"] = "找不到程序"
                    tot += 1
                    continue
                if not os.path.isdir("tmp"):
                    os.mkdir("tmp")
                source_suffix = preFile.split('.')[-1]
                shutil.copyfile(preFile, "tmp/{}.{}".format(pbs["source_name"], source_suffix))
                langDict = Settings["compilers"][langmod]
                langDict.update({ "source": pbs["source_name"], "base_dir": "tmp/" })
                runCommand = langDict["command"].format(**langDict)
                compile_Run = subprocess.Popen(runCommand)
                CompileStart = time.time()
                while True:
                    if (time.time() - CompileStart > 10):
                        compile_Run.kill()
                    if (compile_Run.poll() is None):
                        continue
                    else:
                        break
                if not os.path.isfile("tmp/{}.exe".format(pbs["source_name"])):
                    t[tot]["res"] = "编译错误"
                    t[tot]["score"] = 0
                    t[tot]["info"] = "编译错误"
                    tot += 1
                    continue
                dataPre = dataDir + "\\data\\" + pbs["source_name"] + "\\"
                t[tot]["datas"] = []
                os.chdir("tmp")
                for dts in pbs["data"]:
                    key = random.randint(10000000, 99999999)
                    startTime = time.time()
                    shutil.copyfile(dataPre + dts["in"], "{}.{}".format(pbs["source_name"], "in"))
                    user_Run = subprocess.run('{}.exe'.format(pbs["source_name"]), shell=True, stderr=subprocess.PIPE)
                    endTime = 0
                    MemoryUse = 0
                    judged = 0
                    while True:
                        is_run = 0
                        endTime = time.time()
                        try:
                            pRun = psutil.Process(user_Run.pid)
                            muse = pRun.memory_info().rss / 1024
                        except Exception as e:
                            break
                        else:
                            if muse > MemoryUse:
                                MemoryUse = muse
                        if (MemoryUse > memory_limit):
                            os.killpg(user_Run.pid,signal.SIGUSR1)
                            judged = 1
                            t[tot]["datas"].append({
                                "res": "内存超限",
                                "score": 0,
                                "time": endTime - startTime,
                                "memory": MemoryUse
                            })
                            scs["used_time"] += endTime - startTime
                            break
                        if (endTime - startTime >= time_limit):
                            os.killpg(user_Run.pid,signal.SIGUSR1)
                            judged = 1
                            t[tot]["datas"].append({
                                "res": "时间超限",
                                "score": 0,
                                "time": endTime - startTime,
                                "memory": MemoryUse
                            })
                            scs["used_time"] += endTime - startTime
                            break
                        if (user_Run.poll() is None):
                            is_run = 1
                        if not is_run:
                            break
                    if (judged):
                        continue
                    if user_Run.returncode != 0:
                        judged = 1
                        t[tot]["datas"].append({
                            "res": "运行错误",
                            "score": 0,
                            "time": endTime - startTime,
                            "memory": MemoryUse
                        })
                        scs["used_time"] += endTime - startTime
                        continue
                    shutil.copyfile(dataPre + dts["out"], "{}_{}.{}".format(pbs["source_name"], key, 'out'))
                    diff_val = os.system('diff {}.out {}_{}.out --ignore-space-change --text --brief>diff.txt'.format(pbs["source_name"], pbs["source_name"], key))
                    if diff_val > 0:
                        judged = 1
                        t[tot]["datas"].append({
                            "res": "答案错误",
                            "score": 0,
                            "time": endTime - startTime,
                            "memory": MemoryUse
                        })
                        scs["used_time"] += endTime - startTime
                        continue
                    judged = 1
                    t[tot]["datas"].append({
                        "res": "正确",
                        "score": dts["score"],
                        "time": endTime - startTime,
                        "memory": MemoryUse                        
                    })
                    scs["used_time"] += endTime - startTime
                    scs["score"] += (int)(dts["score"])
                    t[tot]["score"] += (int)(dts["score"])
                    view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
                tot += 1
                os.chdir("..")
                shutil.rmtree("tmp")
                view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
            scs["detailed"] = t
            judged_res.append(scs)
            view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
        Contest_Data["sources"] = judged_res
    view.page().runJavaScript("nomel_main.isJudge = 0")
    view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
    saveFile = Contest_Data["dir"]
    with open(saveFile, 'w', encoding="utf8") as f:
        f.write(json.dumps(Contest_Data, sort_keys=True, indent=4, separators=(',', ':')))

class CallHandler(QObject):

    def __init__(self):
        super(CallHandler, self).__init__()
    @pyqtSlot(str, result=str)
    def judge_start(self, jm):
        self.get_sources("2333")
        thread = threading.Thread(target=run_code, args = (jm,))
        thread.start()

    @pyqtSlot(str, result=str)
    def get_sources(self, a):
        global Contest_Data
        global Settings
        dataDir = Contest_Data["dir"].replace("/", "\\").split("\\")[::-1]
        dataDir.pop(0)
        dataDir = '\\'.join(dataDir[::-1])
        dataDir = dataDir + "\\source"
        if not os.path.isdir(dataDir):
            os.mkdir(dataDir)
        inouts = os.listdir(dataDir)
        Contest_Data["sources"] = []
        det_s = []
        for ia in range(0, len(Contest_Data["problems"])):
            det_s.append({
                "score": "未评测"
            })
        for ifl in inouts:
            if os.path.isdir(dataDir + "\\" + ifl):
                Contest_Data["sources"].append({
                    "name": ifl,
                    "score": "未评测",
                    "detailed": det_s,
                    "user_time": "未评测",
                    "test_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                })
        view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
        saveFile = Contest_Data["dir"]
        with open(saveFile, 'w', encoding="utf8") as f:
            f.write(json.dumps(Contest_Data, sort_keys=True, indent=4, separators=(',', ':')))
    @pyqtSlot(int, result=str)
    def get_data(self, problem_id):
        global Contest_Data
        global Settings
        pb = Contest_Data["problems"][problem_id]
        problem_title = pb["source_name"]
        dataDir = Contest_Data["dir"].replace("/", "\\").split("\\")[::-1]
        dataDir.pop(0)
        dataDir = '\\'.join(dataDir[::-1])
        dataDir = dataDir + "\\data"
        if not os.path.isdir(dataDir):
            os.mkdir(dataDir)
        problemDataDir = dataDir + "\\" + problem_title
        if not os.path.isdir(problemDataDir):
            os.mkdir(problemDataDir)
        inouts = os.listdir(problemDataDir)
        for ifl in inouts:
            if ifl.split(".")[-1] == "ans":
                os.rename(problemDataDir + "\\" + ifl, problemDataDir + "\\" + ifl.replace("ans", "out"))
        inouts = os.listdir(problemDataDir)
        for ifl in inouts:
            if ifl.split(".")[-1] == "in":
                ofl = ifl.replace("in", "out")
                if os.path.isfile(problemDataDir + "\\" + ofl):
                    Contest_Data["problems"][problem_id]["data"].append({
                        "in": ifl,
                        "out": ofl,
                        "time_limit": 1000,
                        "memory_limit": 131072,
                        "subtask": 0,
                        "score": 1,
                    })
        view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
        saveFile = Contest_Data["dir"]
        with open(saveFile, 'w', encoding="utf8") as f:
            f.write(json.dumps(Contest_Data, sort_keys=True, indent=4, separators=(',', ':')))
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
        #print(str_args)
        if (str_args == 'New Contest'):
            saveFile = QFileDialog.getSaveFileName(view,
            "保存比赛文件",
            os.getcwd(),
            "JSON Files (*.json)")
            try:
                saveFile = saveFile[0]
                if len(saveFile) == 0:
                    return 'breaked'
                Contest_Data["dir"] = saveFile.replace("/", "\\")
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
                Contest_Data["dir"] = saveFile.replace("/", "\\")
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
    view.setWindowTitle("Nomel Judge")
    channel = QWebChannel()
    handler = CallHandler()
    channel.registerObject('PyHandler', handler)
    view.page().setWebChannel(channel)
    view.load(
        QUrl(QFileInfo("./index.html").absoluteFilePath()))
    view.show()
    sys.exit(app.exec_())

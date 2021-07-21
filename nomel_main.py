#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
import time
import json
import shutil
import subprocess
import random
import threading
import psutil
import stat

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
    if (jm == 'all'):
        gfbsuf = 0
        for scs in Contest_Data["sources"]:
            view.page().runJavaScript("nomel_main.showingUserId = {}".format(gfbsuf))
            gfbsuf += 1
            scs["score"] = 0
            scs["used_time"] = 0
            tot = 0
            t = []
            for ia in range(0, len(Contest_Data["problems"])):
                t.append({
                    "score": "未评测"
                })
            for pbs in Contest_Data["problems"]:
                #print(pbs)
                langmod = -1
                preFile = dataDir + "\\source\\" + scs["name"] + "\\" + pbs["source_name"]
                #print(preFile)
                if os.path.isfile(preFile + ".cpp"):
                    langmod = 0
                    preFile += ".cpp"
                elif os.path.isfile(preFile + ".c"):
                    langmod = 1
                    preFile += ".c"
                t[tot]["score"] = 0
                scs["detailed"] = t
                if langmod == -1:
                    t[tot]["res"] = "找不到程序"
                    t[tot]["score"] = 0
                    t[tot]["info"] = "找不到程序"
                    tot += 1
                    continue
                os.chmod("tmp", stat.S_IRWXO + stat.S_IRWXG + stat.S_IRWXU)
                if os.path.isdir("tmp"):
                    shutil.rmtree("tmp")
                os.mkdir("tmp")
                source_suffix = preFile.split('.')[-1]
                try:
                    shutil.copyfile(preFile, "tmp/{}.{}".format(pbs["source_name"], source_suffix))
                except Exception as e:
                    t[tot]["res"] = "系统错误"
                    t[tot]["score"] = 0
                    tot += 1
                    continue
                if os.path.exists("tmp/{}.exe".format(pbs["source_name"])):
                    os.remove("tmp/{}.exe".format(pbs["source_name"]))
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
                    view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
                    key = random.randint(10000000, 99999999)
                    try:
                        startTime = time.time()
                        shutil.copyfile(dataPre + dts["in"], "{}.{}".format(pbs["source_name"], "in"))
                        user_Run = subprocess.Popen('{}.exe'.format(pbs["source_name"]), shell=True, stderr=subprocess.PIPE)
                        #print(user_Run.pid)
                        endTime = 0
                        MemoryUse = 0
                        judged = 0
                        rcode = 0
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
                            if (user_Run.poll() is None):
                                is_run = 1
                            if (MemoryUse > (int)(dts["memory_limit"])):
                                os.system("taskkill /F /PID {} /T".format(user_Run.pid))
                                judged = 1
                                t[tot]["datas"].append({
                                    "res": "内存超限",
                                    "score": 0,
                                    "time": endTime - startTime,
                                    "memory": MemoryUse
                                })
                                scs["used_time"] += endTime - startTime
                                break
                            if (endTime - startTime >= (int)(dts["time_limit"]) + 0.2):
                                #os.killpg(user_Run.pid,signal.SIGUSR1)
                                #user_Run.kill()
                                os.system("taskkill /F /PID {} /T".format(user_Run.pid))
                                judged = 1
                                t[tot]["datas"].append({
                                    "res": "时间超限",
                                    "score": 0,
                                    "time": endTime - startTime,
                                    "memory": MemoryUse
                                })
                                scs["used_time"] += endTime - startTime
                                break
                            if not is_run:
                                break
                        if (judged):
                            continue
                        user_Run.wait()
                        rcode = user_Run.returncode
                        if rcode != 0:
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
                    except Exception as e:
                        judged = 1
                        t[tot]["datas"].append({
                            "res": "系统错误",
                            "score": 0,
                            "time": endTime - startTime,
                            "memory": MemoryUse
                        })
                        scs["used_time"] += endTime - startTime
                        continue
                    else:
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
                tot += 1
                os.chdir("..")
                view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
            scs["detailed"] = t
            view.page().runJavaScript("nomel_main.loadContest({})".format(Contest_Data))
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
                        "time_limit": 1,
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

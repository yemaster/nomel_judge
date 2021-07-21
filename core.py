import os
import sys
from time import time
import json
import shutil
import psutil
import random
import subprocess

Settings = {}
with open('config.json', 'r') as fp:
    Settings = json.load(fp)

def nomel_main():
    key = random.randint(10000000, 99999999)
    problem_name = sys.argv[1]
    source_file = sys.argv[2]
    source_lang = (int)(sys.argv[3])
    data_input = sys.argv[4]
    data_output = sys.argv[5]
    time_limit = (float)(sys.argv[6]) + 0.2
    memory_limit = (float)(sys.argv[7])

    source_suffix = source_file.split('.')[-1]

    langDict = Settings["compilers"][source_lang]
    langDict.update({ "source": problem_name, "base_dir": "tmp/" })
    runCommand = langDict["command"].format(**langDict)

    if os.path.isdir("tmp"):
        shutil.rmtree("tmp")
    os.mkdir("tmp")
    
    shutil.copyfile(source_file, "tmp/{}.{}".format(problem_name, source_suffix))
    if (data_input != 'BY'):
        shutil.copyfile(data_input, "tmp/{}.{}".format(problem_name, 'in'))
        shutil.copyfile(data_output, "tmp/{}_{}.{}".format(problem_name, key, 'out'))
    compile_Run = subprocess.Popen(runCommand)
    CompileStart = time()
    while True:
        if (time() - CompileStart > 10):
            compile_Run.kill()
        if (compile_Run.poll() is None):
            continue
        else:
            break
    if not os.path.isfile("tmp/{}.exe".format(problem_name)):
        return ("Compile Error", 0, 0, 1)
    if (data_input == 'BY'):
        return ("Compile OK", 0, 0, 0)
    os.chdir("tmp")
    startTime = time()
    user_Run = subprocess.Popen('{}.exe'.format(problem_name), shell=True, stderr=subprocess.PIPE)
    endTime = 0
    MemoryUse = 0
    while True:
        is_run = 0
        endTime = time()
        try:
            pRun = psutil.Process(user_Run.pid)
            muse = pRun.memory_info().rss / 1024
        except Exception as e:
            break
        else:
            if muse > MemoryUse:
                MemoryUse = muse
        if (MemoryUse > memory_limit):
            user_Run.kill()
            return ("Memory Limit Exceeded", endTime - startTime  , MemoryUse, 5)
        if (endTime - startTime >= time_limit):
            user_Run.kill()
            return ("Time Limit Exceeded", endTime - startTime  , MemoryUse, 4)
        if (user_Run.poll() is None):
            is_run = 1
        if not is_run:
            break
    if 0 != 0:
        return ("Runtime Error", endTime - startTime, MemoryUse, 3)
    diff_val = os.system('diff {}.out {}_{}.out --ignore-space-change --text --brief>diff.txt'.format(problem_name, problem_name, key))
    if diff_val > 0:
        return ("Wrong Answer", endTime - startTime  , MemoryUse, 2)
    return ("Accepted", endTime - startTime  , MemoryUse, 0)

runRes = nomel_main()
print("Result: ", runRes[0])
print("Time_Used", runRes[1], "s")
print("Memory_Used", runRes[2], "KB")
sys.exit(runRes[3])
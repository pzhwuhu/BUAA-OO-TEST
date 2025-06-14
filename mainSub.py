import time
from subprocess import STDOUT, PIPE
from functools import lru_cache
import glob
import os
from colorama import Fore, Back, Style
import sympy

from generate import preTreatment
from run_java import execute_java
from run_java import execute_py

@lru_cache(maxsize=None)
def calculate(string):
    return sympy.expand(preTreatment(string))

@lru_cache(maxsize=None)
def evaluate(myAns, poly, name):
    # 用符号计算验证待测程序输出与参考答案是否一致
    x = sympy.Symbol('x')
    out, t = execute_java(poly, name)
    subString = "0\n0\n(" + myAns + ")-(" + out + ")"
    sub, t2 = execute_java(subString, "hw_3.jar")
    subAns = calculate(sub)
    if subAns == 0:
        print(name + ": " + Fore.GREEN + "Accepted" + Fore.WHITE)
        return True, t
    else:
        print(name + ": " + Fore.RED + "Wrong\n" + Fore.WHITE)
        print("Input:")
        print(poly)
        print("Origin:")
        print(myAns)
        print("User Answer:")
        print(out)
        return False, t

print("============ INITIALIZATION ============")
directory = './'
jar_files = glob.glob(os.path.join(directory, '*.jar'))
for jar_file in jar_files:
    print(jar_file)

i = 0
while True:
    i += 1
    print("-------------------------->   epoch " + str(i))
    poly = execute_py("", "generate.py")
    print(poly)
    myAns, t = execute_java(poly, "hw_3.jar")
    for jar_file in jar_files:
        try:
            res, t = evaluate(myAns, poly, str(os.path.basename(jar_file)))
            if not res:
                exit()
            pass
        except Exception as e:
            print("Origin Input: \n" + poly)
            print(os.path.basename(jar_file) + ": no output or output is illegal")
            exit()

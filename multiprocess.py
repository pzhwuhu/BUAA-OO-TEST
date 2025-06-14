import threading
import time
import glob
import os
from multiprocessing.pool import worker

from colorama import Fore, Back, Style
import error
import generate
import sys
import evaluate
import func_timeout

wrong = 0
tle = 0

def fun(input_str, name, jar_file, interact):
    global wrong
    global tle
    try:
        res, T_run, WT, W, run_time = evaluate.evaluate(input_str, name)
        if (interact):
            if (res == False):
                print(str(name) + ": " + Fore.RED + "Wrong or TLE" + Fore.WHITE)
                wrong += 1
            else:
                print(str(name) + ": " + Fore.GREEN + "Accepted" + Fore.WHITE + " with " + str(run_time) + "s\nT_run: " + str(T_run) + " WT: " + str(WT) + " W: " + str(W))
        elif (res == False):
            wrong += 1
    except func_timeout.exceptions.FunctionTimedOut as e:
        tle += 1
        if (interact):
            print(str(os.path.basename(jar_file)) + ": " + Fore.WHITE + "Prase Time Limit Exceeded" + Fore.WHITE)
    except Exception as e:
        wrong += 1
        if (interact):
            print(str(os.path.basename(jar_file)) + ": " + Fore.RED + "Error" + Fore.WHITE)
        error.error_output(name, "Unkown Error", input_str, "", e)
def multi_process(jar_files, interact):
    test_case = 0
    wrong = 0
    tle = 0

    # 打开日志文件
    with open("process_log.txt", "a") as log_file:
        while True:
            test_case += 1
            log_file.write(f"---->   epoch {test_case}   ---   wrong: {wrong}   ---   tle: {tle}   <----\n")
            if interact:
                print(f"---->   epoch {test_case}   ---   wrong: {wrong}   ---   tle: {tle}   <----")

            input_str, command_number = generate.generate_input()
            log_file.write(f"Generated input:\n{input_str}\n")
            if interact:
                print("input lines:" + str(command_number))
                print(input_str)

            with open("stdin.txt", "w") as f:
                f.write(input_str)
            # with open("stdin.txt", "r") as f:
            #     input_str = f.read()
            threads = []
            for jar_file in jar_files:
                if os.name == 'nt':
                    name = os.path.splitext(jar_file)[0].split("\\")[1]
                else:
                    name = os.path.splitext(jar_file)[0].split("/")[1]

                def thread_target():
                    nonlocal wrong, tle
                    try:
                        res, T_run, WT, W, run_time = evaluate.evaluate(input_str, name)
                        if res == False:
                            log_file.write(f"{name}: Wrong or TLE\n")
                            if interact:
                                print(str(name) + ": " + Fore.RED + "Wrong or TLE" + Fore.WHITE)
                            wrong += 1
                        else:
                            log_file.write(f"{name}: Accepted with {run_time}s\nT_run: {T_run} WT: {WT} W: {W}\n")
                            if interact:
                                print(str(name) + ": " + Fore.GREEN + "Accepted" + Fore.WHITE + " with " + str(run_time) + "s\nT_run: " + str(T_run) + " WT: " + str(WT) + " W: " + str(W) + "\n")
                    except func_timeout.exceptions.FunctionTimedOut as e:
                        tle += 1
                        log_file.write(f"{os.path.basename(jar_file)}: Parse Time Limit Exceeded\n")
                        if interact:
                            print(str(os.path.basename(jar_file)) + ": " + Fore.WHITE + "Parse Time Limit Exceeded" + Fore.WHITE)
                    except Exception as e:
                        wrong += 1
                        log_file.write(f"{os.path.basename(jar_file)}: Error - {str(e)}\n")
                        if interact:
                            print(str(os.path.basename(jar_file)) + ": " + Fore.RED + "Error" + Fore.WHITE)
                        error.error_output(name, "Unknown Error", input_str, "", e)

                thread = threading.Thread(target=thread_target)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            log_file.write("\n")
            if interact:
                print("")
            else:
                with open("matcher.log", "w") as f:
                    f.write(f"epoch: {test_case} Wrong: {wrong} TLE: {tle}\n")

            time.sleep(0.5)

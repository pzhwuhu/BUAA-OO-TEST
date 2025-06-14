import error
import generate
import evaluate
import func_timeout
import time
import os
from colorama import Fore, Back, Style

def single_process(jar_files, interact):
    test_case = 0
    wrong = 0
    tle = 0

    # 打开日志文件
    with open("process_log.txt", "a") as log_file:
        while True:
            test_case += 1
            log_file.write(f"---->   epoch {test_case}   ---   wrong: {wrong}   ---   tle: {tle}   <----\n")
            print(f"---->   epoch {test_case}   ---   wrong: {wrong}   ---   tle: {tle}   <----")

            input_str, command_number = generate.generate_input()
            log_file.write(f"Generated input:\n{input_str}\n")
            print("input lines:" + str(command_number))
            print(input_str)
            
            with open("stdin.txt", "w") as f:
                f.write(input_str)
            with open("stdin.txt", "r") as f:
                input_str = f.read()
            for jar_file in jar_files:
                if (os.name == 'nt'):
                    name = os.path.splitext(jar_file)[0].split("\\")[1]
                else:
                    name = os.path.splitext(jar_file)[0].split("/")[1]

                try:
                    res, T_run, WT, W, run_time  = evaluate.evaluate(input_str, name)
                    if res == False:
                        log_file.write(f"{name}: Wrong or TLE\n")
                        print(str(name) + ": " + Fore.RED + "Wrong or TLE" + Fore.WHITE)
                        wrong += 1
                    else:
                        log_file.write(f"{name}: Accepted with {run_time}s\nT_run: {T_run} WT: {WT} W: {W}\n")
                        print(str(name) + ": " + Fore.GREEN + "Accepted" + Fore.WHITE + " with " + str(run_time) + "s\nT_run: " + str(T_run) + " WT: " + str(WT) + " W: " + str(W))
                except func_timeout.exceptions.FunctionTimedOut as e:
                    tle += 1
                    log_file.write(f"{os.path.basename(jar_file)}: Parse Time Limit Exceeded\n")
                    print(str(os.path.basename(jar_file)) + ": " + Fore.WHITE + "Parse Time Limit Exceeded" + Fore.WHITE)
                except Exception as e:
                    wrong += 1
                    log_file.write(f"{os.path.basename(jar_file)}: Error - {str(e)}\n")
                    print(str(os.path.basename(jar_file)) + ": " + Fore.RED + "Error" + Fore.WHITE)
                    error.error_output(name, "Unknown Error", input_str, "", e)
            log_file.write("\n")
            print("")
            time.sleep(0.5)

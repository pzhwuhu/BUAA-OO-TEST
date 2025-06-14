import json
from random import random,randint,shuffle,choice

config = json.load(open('config.json'))
command_num_max = int(config['command_num_max'])

id = -20
command_list = ["ap", "ar", "mr", "at", "dt",
                "att", "dft", "qv", "qci", "qts",
                "qtav", "qba"]
def genOneCommand():
    global command_list
    p = random()
    if p < 0.2:
        return ap()
    elif p < 0.45:
        return ar()
    else:
        command = choice(command_list)
        if command == "ap":
            return ap()
        elif command == "ar":
            return ar()
        elif command == "mr":
            return mr()
        elif command == "at":
            return at()
        elif command == "dt":
            return dt()
        elif command == "att":
            return att()
        elif command == "dft":
            return dft()
        elif command == "qv":
            return qv()
        elif command == "qci":
            return qci()
        elif command == "qts":
            return qts()
        elif command == "qtav":
            return qtav()
        elif command == "qba":
            return qba()
    '''
    elif p < 0.55:
        return mr()
    elif p < 0.7:
        return qci()
     elif p < 0.85:
         return qbs()
    else:
        return qts()
    '''

def ap():
    global id
    instr = "ap " + str(id) + " " + genName() + " " + str(genAge())
    id = id + 1
    return instr

def ar():
    instr = "ar " + str(genId()) + " " + str(genId()) + " " + str(genValue())
    return instr

def mr():
    instr = "mr " + str(genId()) + " " + str(genId()) + " " + str(genModifyValue())
    return instr

def at():
    instr = "at " + str(genId()) + " " + str(genId())
    return instr

def dt():
    instr = "dt " + str(genId()) + " " + str(genId())
    return instr

def att():
    instr = "att " + str(genId()) + " " + str(genId()) + " " + str(genId())
    return instr

def dft():
    instr = "dft " + str(genId()) + " " + str(genId()) + " " + str(genId())
    return instr

def qv():
    instr = "qv " + str(genId()) + " " + str(genId())
    return instr

def qci():
    instr = "qci " + str(genId()) + " " + str(genId())
    return instr


def qtav():
    instr = "qtav " + str(genId()) + " " + str(genId())
    return instr


def qba():
    instr = "qba " + str(genId())
    return instr

def qbs():
    instr = "qbs"
    return instr


def qts():
    instr = "qts"
    return instr


def genCommands():
    commands = ""
    if random() < 0.5:
        commands = commands + load_network() + "\n"
    p = random()
    if p < 0.3:
        command_num = randint(0, command_num_max) + 1
    elif p < 0.85 :
        command_num = randint(int(command_num_max / 2), command_num_max) + 1
    else :
        command_num = randint(int(command_num_max / 5 * 4), command_num_max) + 1
    for i in range(command_num):
        commands = commands + genOneCommand() + "\n"
    return commands


def load_network():
    global id
    res, tmp = [], []
    p = random()
    n = 100
    # if p < 0.1:
    #     n = randint(1, 100)
    # elif p < 0.4:
    #     n = randint(100, 200)
    # else:
    #     n = randint(200, 300)

    res.append(f'ln {n}')
    ids = [i for i in range(id, id + n)]
    id = id + n
    shuffle(ids)

    for i in range(n):
        tmp.append(ids[i])
    res.append(' '.join(map(str, tmp)))

    tmp = []
    for i in range(n):
        tmp.append(genName())
    res.append(' '.join(map(str, tmp)))


    tmp = []
    for i in range(n):
        tmp.append(str(genAge()))
    res.append(' '.join(map(str, tmp)))

    for i in range(1, n):
        tmp = []
        for j in range(i):
            if (random() < 0.95):
                tmp.append(str(genValue()))
            else:
                tmp.append(0)
        res.append(' '.join(map(str, tmp)))

    return '\n'.join(res)

def genId():
    global id
    if random() < 0.8:
        return randint(-20, id)
    else:
        return randint(-10, 10)


def genName():
    return "name" + str(randint(0, 1000))

def genAge():
    # return randint(1, 200)
    return 1

def genValue():
    return randint(1, 100)

def genModifyValue():
    p = random()
    if p < 0.6:
        return randint(0, 200)
    elif p < 0.8:
        return randint(-200, 0)
    else:
        return randint(-100, 100)

def genHardRelationCommands():
    commands = ""
    commands = commands + load_network() + "\n"
    command_num = int(config["command_num_max"])
    for i in range(0,command_num // 2, 2):
        commands = commands + ap() + "\n"
        commands = commands + ar() + "\n"
    for i in range(command_num // 2, command_num, 3):
        commands = commands + mr() + "\n"
        commands = commands + mr() + "\n"
        commands = commands + qts() + "\n"
    return commands

def genHardTagCommands():
    commands = ""
    return commands

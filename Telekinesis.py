# -*- coding: utf-8 -*-
import time
import json
import os
import nbt

# ========= 配置参数开始 =========
# 指令前綴
Prefix = '!!tp'

# 请求后几秒自动拒绝
tpRequestTimeout = 30

# 同意请求后等待几秒传送(<=0代表不等待)
waitTpForRequest = 0

# 服务端工作目录（相对位置）
serverLocation = 'server'

# 插件配置文件目录名
configDirectory = 'Telekinesis'

# ========= 配置参数结束 =========
PLUGIN_METADATA = {
    'id': 'telekinesis',
    'version': '0.0.2',
    'name': 'Telekinesis',
    'description': 'Another Teleport Helper',
	'dependencies': {
		'minecraft_data_api': '*',
        'online_player_api': '*'
	}
}

getPos = 'no'
SpawnPos = []

def readSpawnPos():
    nbtData = nbt.nbt.NBTFile(f"{serverLocation}/world/level.dat", 'rb')
    nbtData = nbtData["Data"]
    readSpawnPos.result = [nbtData["SpawnX"].value, nbtData["SpawnY"].value, nbtData["SpawnZ"].value]

def getTpList():
    f = open(f"plugins/{configDirectory}/requests.json",'r',encoding='utf8')
    data = json.load(f)
    f.close()
    return data

def writeTpList(data):
    f = open(f"plugins/{configDirectory}/requests.json",'w',encoding='utf8')
    json.dump(data,f)
    f.close()

def getLastTpPosList():
    f = open(f"plugins/{configDirectory}/lastPos.json",'r',encoding='utf8')
    data = json.load(f)
    f.close()
    return data

def getLastTpPos(name,drop=False):
    data = getLastTpPosList()
    if name in data:
        pos = data[name]
        if drop==True:
            del data[name]
            writeLastTpPosList(data)
        return pos
    else:
        return []

def writeLastTpPos(name,x,y,z):
    data = getLastTpPosList()
    data[name] = [x,y,z]
    writeLastTpPosList(data)
    
def findBy(tag,name):
    tplist = getTpList()
    for tp in tplist:
        if name == tp[tag]:
            return tp
    return None

def create_req(server,info,name,to):
    # 新增传送请求
    tplist = getTpList()
    tplist.append({'name':name,'to':to,'status':'wait'})
    writeTpList(tplist)
    
    # 传送请求文字
    timeout = tpRequestTimeout
    print_message(server,info,f"已向玩家 {to} 发送传送请求")
    server.tell(to,f"§d[Telekinesis] §6玩家 {name} 想传送到你身边")
    server.tell(to,f"§d[Telekinesis] §6在 {timeout} 秒内输入 {Prefix} yes 同意， 输入 {Prefix} no 拒绝")
    
    # 等待回复
    while timeout>0:
        req = findBy('name',name)
        if req['status']=='wait':
            # 未回复，继续等待
            time.sleep(1)
            timeout -= 1
        elif req['status']=='yes':
            # 同意
            if waitTpForRequest != 0:
                server.tell(to,f"§d[Telekinesis] §6已同意来自玩家 {name} 的传送请求， 将在 {waitTpForRequest} 秒后开始传送")
            else:
                server.tell(to,f"§d[Telekinesis] §6已同意来自玩家 {name} 的传送请求， 正在传送")
            server.tell(name,f"§d[Telekinesis] §6玩家 {to} 已同意传送请求")
            tpAfterSeconds(server,name,to,waitTpForRequest)
            break
        elif req['status']=='no':
            # 不同意
            server.tell(to,f"§d[Telekinesis] §6已拒绝来自玩家 {name} 的传送请求， 取消传送")
            server.tell(name,f"§d[Telekinesis] §6{to} 拒绝了传送请求")
            break
    
    # 请求等待超时
    if timeout==0 and tpRequestTimeout!=0:
        server.tell(to,f"§d[Telekinesis] §6来自玩家 {name} 的传送请求已超时")
        server.tell(name,f"§d[Telekinesis] §6玩家 {to} 超时未回复， 传送请求已被系统取消")
    
    # 删除传送请求
    delete_req(name)

def writeLastTpPosList(data):
    f = open(f"plugins/{configDirectory}/lastPos.json",'w',encoding='utf8')
    json.dump(data,f)
    f.close()

def responseTpRequests(to,answer):
    tplist = getTpList()
    for tp in tplist:
        if to == tp['to']:
            tp['status'] = answer
    writeTpList(tplist)

def tpAfterSeconds(server,name,to,sec=5):
    global getPos
    while sec>0:
        server.tell(name,f"§d[Telekinesis] §6即将开始传送， 将在 {sec} 秒后传送到到玩家 {to} 身边")
        time.sleep(1)
        sec -= 1
    getPos = name # name -> getPos
    server.execute(f"/execute positioned as {name} run tp {name} ~0 ~0 ~0")
    time.sleep(0.05)
    server.execute(f"/tp {name} {to}")

def delete_req(name):
    tplist = getTpList()
    find = -1
    for idx,tp in enumerate(tplist):
        if name == tp['name']:
            find = idx
    if find!=-1:
        tplist.pop(find)
        writeTpList(tplist)

def on_info(server, info):
    if not info.is_user:
        global getPos
        if "Teleported" in info.content and getPos!='no':
            cmdList = info.content.split(' ')
            if getPos == cmdList[1]:
                x = cmdList[3].split('.')[0]
                y = cmdList[4].split('.')[0]
                z = cmdList[5].split('.')[0]
                writeLastTpPos(getPos,x,y,z)
        getPos = 'no'
        return
    
    command = info.content.split()
    if len(command) == 0 or command[0] != Prefix:
        return
    cmd_len = len(command)

    try:
        # !!tp
        if cmd_len == 1:
            show_help(server,info)
        # !!tp help/<playername>/yes/no
        elif cmd_len ==2:
            if command[1].lower()=='help':
                # !!tp help
                show_help(server,info)
            elif command[1].lower()=='spawn':
                # !!tp spawn
                getPos = info.player # name -> getPos
                server.execute(f"/execute positioned as {info.player} run tp {info.player} ~0 ~0 ~0")
                time.sleep(0.05)
                print_message(server,info,"传送到世界重生点")
                server.execute(f"/tp {info.player} {SpawnPos[0]} {SpawnPos[1]} {SpawnPos[2]}")
            elif command[1].lower() in ['yes','no']:
                # !!tp yes/no
                req = findBy('to',info.player)
                if req==None:
                    print_message(server,info,"目前没有待确认的请求")
                else:
                    responseTpRequests(info.player,command[1].lower())
            elif command[1].lower()=='back':
                pos = getLastTpPos(info.player,True)
                if pos!=[]:
                    print_message(server,info,"正在进行回溯传送")
                    server.execute(f"/tp {info.player} {pos[0]} {pos[1]} {pos[2]}")
                else:
                    print_message(server,info,"您没有可回溯的传送")
            else:
                # !!tp <playername>
                find_player = server.get_plugin_instance('online_player_api').check_online(command[1])
                if find_player==False:
                    print_message(server,info,"请求失败，指定的玩家不存在或未上线")
                elif findBy('name',info.player):
                    print_message(server,info,"请求失败，请先处理现存的传送请求")
                elif findBy('to',command[1]):
                    print_message(server,info,"请求失败，对方仍有待处理传送请求")
                else:
                    create_req(server,info,info.player,command[1])
        else:
            print_message(server,info,"指令输入有误!")
            show_help(server,info)
    except Exception as e:
        #print_message(server,info,str(e))
        print_message(server,info,"内部错误")
        show_help(server,info)

def show_help(server,info):
    print_message(server,info,f'{Prefix} spawn | 传送到世界重生点')
    print_message(server,info,f'{Prefix} back | 进行回溯传送')
    print_message(server,info,f'{Prefix} <玩家> | 请求传送自己到 <玩家> 身边')
    print_message(server,info,f'{Prefix} <yes/no> | 同意/拒绝传送到自己身边的请求')

def print_message(server, info, msg, tell=True, prefix='§d[Telekinesis] §6'):
    msg = prefix + msg
    if info.is_player and not tell:
        server.say(msg)
    else:
        server.reply(info, msg)

def on_load(server, old):
    server.register_help_message(f'{Prefix} help','显示 Telekinesis 帮助')
    if not os.path.exists(f"plugins/{configDirectory}"):
        os.mkdir(f"plugins/{configDirectory}")
    writeTpList([])
    writeLastTpPosList({})
    try:
        readSpawnPos()
    except Exception as e:
        server.logger.warn('level.dat does not exists, command "spawn" will not work.')

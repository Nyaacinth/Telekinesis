# -*- coding: utf-8 -*-
import time
import json
import os
import nbt
import fcntl
import traceback
from mcdreforged.api.decorator import new_thread

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
    'version': '0.1.2',
    'name': 'Telekinesis',
	'dependencies': {
		'minecraft_data_api': '*'
	}
}

# 底层处理用函数

def readSpawnPos(): # 读重生点
    nbtData = nbt.nbt.NBTFile(f"{serverLocation}/world/level.dat", 'rb')
    nbtData = nbtData["Data"]
    readSpawnPos.result = [nbtData["SpawnX"].value, nbtData["SpawnY"].value, nbtData["SpawnZ"].value]

def readReqList(): # 读请求队列
    f = open(f"plugins/{configDirectory}/requests.json",'r',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_SH)
    data = json.load(f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()
    return data

def writeReqList(data): # 写请求队列
    f = open(f"plugins/{configDirectory}/requests.json",'w',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_EX)
    json.dump(data,f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()

def readHomeList(): # 读家园列表
    f = open(f"plugins/{configDirectory}/homes.json",'r',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_SH)
    data = json.load(f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()
    return data

def writeHomeList(data): # 写家园列表
    f = open(f"plugins/{configDirectory}/homes.json",'w',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_EX)
    json.dump(data,f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()

def readLastTpPosList(): # 读回溯传送队列
    f = open(f"plugins/{configDirectory}/lastPos.json",'r',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_SH)
    data = json.load(f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()
    return data

def writeLastTpPosList(data): # 写回溯传送队列
    f = open(f"plugins/{configDirectory}/lastPos.json",'w',encoding='utf8')
    fcntl.flock(f,fcntl.LOCK_EX)
    json.dump(data,f)
    fcntl.flock(f,fcntl.LOCK_UN)
    f.close()

def getPlayerCoordinate(server,player): # 获取玩家坐标（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    coordinate = server.get_plugin_instance('minecraft_data_api').get_player_coordinate(player)
    return coordinate

def getPlayerDimension(server,player): # 获取玩家所处维度（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    dimension = server.get_plugin_instance('minecraft_data_api').get_player_info(player,'Dimension')
    return dimension

def findReqBy(tag,player): # 依赖 readReqList() ，查询是否存在请求
    reqlist = readReqList()
    for tp in reqlist:
        if player == tp[tag]:
            return tp
    return None

def getLastTpPos(player,drop=False): # 依赖 readLastTpPosList() ，查询是否存在可回溯的传送
    data = readLastTpPosList()
    if player in data:
        pos = data[player]
        if drop==True:
            del data[player]
            writeLastTpPosList(data)
        return pos
    else:
        return []

def writeLastTpPos(player,x,y,z,dimension='minecraft:overworld'): # 依赖 readLastTpPosList() ，写入可回溯的传送
    data = readLastTpPosList()
    data[player] = [x,y,z,dimension]
    writeLastTpPosList(data)

def checkPlayerIfOnline(server,player): # 检查玩家在线情况（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    amount, limit, players = server.get_plugin_instance('minecraft_data_api').get_server_player_list()
    if player in players:
        return True
    else:
        return False

def tellMessage(server,info,msg,to=None,tell=True,prefix='§d[Telekinesis] §6'): # 向玩家打印信息
    msg = prefix + msg
    if to is not None:
        if checkPlayerIfOnline(server,to) is True:
            server.tell(to,msg)
    else:
        if info.is_player and not tell:
            server.say(msg)
        else:
            server.reply(info,msg)

def responseTpRequests(to,answer): # 回复传送请求
    reqlist = readReqList()
    for tp in reqlist:
        if to == tp['to']:
            tp['status'] = answer
    writeReqList(reqlist)

def createHome(server,info,sendby,to): # 新增家园传送点
    return # TODO

def deleteReq(player): # 删除传送请求
    reqlist = readReqList()
    find = -1
    for idx,tp in enumerate(reqlist):
        if player == tp['sendby']:
            find = idx
    if find!=-1:
        reqlist.pop(find)
        writeReqList(reqlist)

def createReq(server,info,sendby,to): # 新增传送请求
    reqlist = readReqList()
    reqlist.append({'sendby':sendby,'to':to,'status':'wait'})
    writeReqList(reqlist)

    # 传送请求文字
    timeout = tpRequestTimeout
    tellMessage(server,info,f"已向玩家 {to} 发送传送请求")
    tellMessage(server,info,f"玩家 {sendby} 想传送到你身边",to)
    tellMessage(server,info,f"在 {timeout} 秒内输入 {Prefix} yes 同意， 输入 {Prefix} no 拒绝",to)
    
    # 等待回复
    while timeout>0:
        req = findReqBy('sendby',sendby)
        if req['status']=='wait': # 未回复，继续等待
            time.sleep(1)
            timeout -= 1
        elif req['status']=='yes': # 同意
            if waitTpForRequest != 0:
                tellMessage(server,info,f"已同意来自玩家 {sendby} 的传送请求， 将在 {waitTpForRequest} 秒后开始传送",to)
            else:
                tellMessage(server,info,f"已同意来自玩家 {sendby} 的传送请求， 正在传送",to)
            tellMessage(server,info,f"玩家 {to} 已同意传送请求， 正在传送")
            sec = waitTpForRequest
            while sec>0:
                tellMessage(server,info=None,msg=f"即将开始传送， 将在 {sec} 秒后传送到玩家 {to} 身边",to=sendby)
                time.sleep(1)
                sec -= 1
            coordinate = getPlayerCoordinate(server,player=sendby)
            dimension = getPlayerDimension(server,player=sendby)
            writeLastTpPos(sendby,coordinate.x,coordinate.y,coordinate.z,dimension)
            server.execute(f"/tp {sendby} {to}")
            break
        elif req['status']=='no': # 不同意
            tellMessage(server,info,f"已拒绝来自玩家 {sendby} 的传送请求， 取消传送",to)
            tellMessage(server,info,f"{to} 拒绝了传送请求")
            break
    
    # 请求等待超时
    if timeout==0 and tpRequestTimeout!=0:
        tellMessage(server,info,f"来自玩家 {sendby} 的传送请求已超时",to)
        tellMessage(server,info,f"玩家 {to} 超时未回复， 传送请求已被系统取消")
    
    # 删除传送请求
    deleteReq(sendby)

# 主逻辑（指令逻辑实现）

def show_help(server,info): # 插件帮助，展示可用子命令
    tellMessage(server,info,f"{Prefix} spawn       传送到世界重生点")
    tellMessage(server,info,f"{Prefix} back        进行回溯传送")
    tellMessage(server,info,f"{Prefix} ask <玩家>  请求传送自己到 <玩家> 身边")
    tellMessage(server,info,f"{Prefix} <yes|no>     同意/拒绝传送到自己身边的请求")
    tellMessage(server,info,f"{Prefix} help        展示本帮助信息")
    tellMessage(server,info,f"{Prefix} about       关于")

def show_about(server,info): # 展示插件关于信息
    tellMessage(server,info,'关于信息')
    tellMessage(server,info,f"当前版本： v{PLUGIN_METADATA['version']}",to=None,tell=True,prefix='§6')
    tellMessage(server,info,f"一个小小的传送插件， 维护者： Nyaacinth",to=None,tell=True,prefix='§6')
    tellMessage(server,info,f"在此致谢 dream-rhythm ， 本插件以 tpHelper 的工作基础重写而来",to=None,tell=True,prefix='§6')

@new_thread
def tp_spawn(server,info): # !!tp spawn
    sec = waitTpForRequest
    if sec!=0:
        tellMessage(server,info,f"系统已收到指令， 将在 {sec} 秒后传送到世界重生点")
    while sec>0:
        tellMessage(server,info,f"即将开始传送， 将在 {sec} 秒后执行")
        time.sleep(1)
        sec -= 1
    tellMessage(server,info,"传送到世界重生点")
    coordinate = getPlayerCoordinate(server,player=info.player)
    dimension = getPlayerDimension(server,player=info.player)
    writeLastTpPos(info.player,coordinate.x,coordinate.y,coordinate.z,dimension)
    server.execute(f"/execute in minecraft:overworld run tp {info.player} {readSpawnPos.result[0]} {readSpawnPos.result[1]} {readSpawnPos.result[2]}")

@new_thread
def tp_yesno(server,info,command): # !! tp yes/no
    req = findReqBy('to',info.player)
    if req==None:
        tellMessage(server,info,"目前没有待确认的请求")
    else:
        responseTpRequests(info.player,command[1].lower())

@new_thread
def tp_back(server,info): # !! tp back
    sec = waitTpForRequest
    pos = getLastTpPos(info.player,True)
    if pos!=[]:
        if sec!=0:
            tellMessage(server,info,f"系统已收到指令， 将在 {sec} 秒后回溯传送")
        while sec>0:
            tellMessage(server,info,f"即将开始传送， 将在 {sec} 秒后执行")
            time.sleep(1)
            sec -= 1
        tellMessage(server,info,"正在进行回溯传送")
        coordinate = getPlayerCoordinate(server,player=info.player)
        dimension = getPlayerDimension(server,player=info.player)
        writeLastTpPos(info.player,coordinate.x,coordinate.y,coordinate.z,dimension)
        server.execute(f"/execute in {pos[3]} run tp {info.player} {pos[0]} {pos[1]} {pos[2]}")
    else:
        tellMessage(server,info,"您没有可回溯的传送")

@new_thread
def tp_ask(server,info,command): # !! tp ask <playername>
    if checkPlayerIfOnline(server,command[2])==False:
        tellMessage(server,info,"请求失败，指定的玩家不存在或未上线")
    elif findReqBy('sendby',info.player):
        tellMessage(server,info,"请求失败，请先处理现存的传送请求")
    elif findReqBy('to',command[1]):
        tellMessage(server,info,"请求失败，对方仍有待处理传送请求")
    else:
        createReq(server,info,info.player,command[2])

# 外部回调（主逻辑入口）

def on_load(server, old): # 插件初始化
    server.register_help_message(f'{Prefix} help','显示 Telekinesis 帮助')
    if not os.path.exists(f"plugins/{configDirectory}"):
        os.mkdir(f"plugins/{configDirectory}")
    if not os.path.exists(f"plugins/{configDirectory}/homes.json"):
        writeHomeList([])
    if not os.path.exists(f"plugins/{configDirectory}/lastPos.json"):
        writeLastTpPosList({})
    writeReqList([])
    try:
        readSpawnPos()
    except Exception as e:
        server.logger.warn('cannot read level.dat, command "spawn" will not work.')

def on_user_info(server, info): # 接收输入
    command = info.content.split()
    if len(command) == 0 or command[0] != Prefix:
        return
    command_lenth = len(command)
    try:
        if command_lenth == 1: # !!tp
            show_help(server,info)
        elif command_lenth ==2: # !!tp help/yes/no
            if command[1].lower()=='help': # !!tp help
                show_help(server,info)
            elif command[1].lower()=='about': # !!tp about
                show_about(server,info)
            elif command[1].lower()=='spawn': # !!tp spawn
                tp_spawn(server,info)
            elif command[1].lower() in ['yes','no']: # !!tp yes/no
                tp_yesno(server,info,command)
            elif command[1].lower()=='back': # !!tp back
                tp_back(server,info)
            else:
                tellMessage(server,info,"指令输入有误!")
                show_help(server,info)
        elif command_lenth ==3: # !!tp ask <playername>
            if command[1].lower()=='ask': # !!tp ask
                tp_ask(server,info,command)
            else:
                tellMessage(server,info,"指令输入有误!")
                show_help(server,info)
        else:
            tellMessage(server,info,"指令输入有误!")
            show_help(server,info)
    except Exception as e:
        tellMessage(server,info,"内部错误")
        print(traceback.format_exc())
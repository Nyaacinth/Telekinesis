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
    'version': '0.1.1',
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
    dimension = server.get_plugin_instance('minecraft_data_api').get_player_dimension(player)
    return dimension

def getPlayerUUID(server,player): # 获取玩家UUID（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    uuid = server.get_plugin_instance('minecraft_data_api').get_player_info(player,'UUID')
    print(uuid)
    return

def tellMessage(server,info,msg,tell=True,prefix='§d[Telekinesis] §6'): # 向玩家打印信息
    msg = prefix + msg
    if info.is_player and not tell:
        server.say(msg)
    else:
        server.reply(info, msg)

def findReqBy(tag,uuid): # 依赖 readReqList() ，查询是否存在请求
    reqlist = readReqList()
    for tp in reqlist:
        if uuid == tp[tag]:
            return tp
    return None

def getLastTpPos(name,drop=False): # 依赖 readLastTpPosList() ，查询是否存在可回溯的传送
    data = readLastTpPosList()
    if name in data:
        pos = data[name]
        if drop==True:
            del data[name]
            writeLastTpPosList(data)
        return pos
    else:
        return []

def writeLastTpPos(name,x,y,z): # 依赖 readLastTpPosList() ，写入可回溯的传送
    data = readLastTpPosList()
    data[name] = [x,y,z]
    writeLastTpPosList(data)

# 主逻辑（指令逻辑实现）

def show_help(server,info): # 插件帮助，展示可用子命令
    tellMessage(server,info,f'{Prefix} spawn | 传送到世界重生点')
    tellMessage(server,info,f'{Prefix} back | 进行回溯传送')
    tellMessage(server,info,f'{Prefix} ask <玩家> | 请求传送自己到 <玩家> 身边')
    tellMessage(server,info,f'{Prefix} here <玩家> | 请求 <玩家> 传送到自己身边')
    tellMessage(server,info,f'{Prefix} <yes/no> | 同意/拒绝传送到自己身边的请求')

@new_thread
def tp_spawn(server,info): # !!tp spawn
    tellMessage(server,info,"传送到世界重生点")
    coordinate = getPlayerCoordinate(server,player=info.player)
    writeLastTpPos(info.player,coordinate.x,coordinate.y,coordinate.z)
    server.execute(f"/tp {info.player} {readSpawnPos.result[0]} {readSpawnPos.result[1]} {readSpawnPos.result[2]}")

@new_thread
def tp_yesno(server,info): # !! tp yes/no
    req = findReqBy('to',info.player)
    if req==None:
        tellMessage(server,info,"目前没有待确认的请求")
    else:
        responseTpRequests(info.player,command[1].lower())

@new_thread
def tp_back(server,info): # !! tp back
    pos = getLastTpPos(info.player,True)
    if pos!=[]:
        tellMessage(server,info,"正在进行回溯传送")
        coordinate = getPlayerCoordinate(server,player=info.player)
        writeLastTpPos(info.player,coordinate.x,coordinate.y,coordinate.z)
        server.execute(f"/tp {info.player} {pos[0]} {pos[1]} {pos[2]}")
    else:
        tellMessage(server,info,"您没有可回溯的传送")

@new_thread
def tp_ask(server,info,command): # !! tp ask <playername>
    return # TODO

@new_thread
def tp_here(server,info): # !! tp here <playername>
    return # TODO

# 外部回调（主逻辑入口）

def on_load(server, old): # 插件初始化
    server.register_help_message(f'{Prefix} help','显示 Telekinesis 帮助')
    if not os.path.exists(f"plugins/{configDirectory}"):
        os.mkdir(f"plugins/{configDirectory}")
        writeLastTpPosList({})
    writeReqList([])
    try:
        readSpawnPos()
    except Exception as e:
        server.logger.warn('level.dat does not exists, command "spawn" will not work.')

# 此处 on_user_info 用于替代暂时找不到文档的 command tree 注册，什么时候有文档了就更换实现
# 另：由于 on_death_message 事件被移除（1.x 起）且暂无替代品，死亡回溯功能暂不实现
# 另之二：MCDReforged 搞 快 点 （逃
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
            elif command[1].lower()=='spawn': # !!tp spawn
                tp_spawn(server,info)
            elif command[1].lower() in ['yes','no']: # !!tp yes/no
                tp_yesno(server,info)
            elif command[1].lower()=='back': # !!tp back
                tp_back(server,info)
            else:
                tellMessage(server,info,"指令输入有误!")
                show_help(server,info)
        elif command_lenth ==3: # !!tp ask/here <playername>
            if command[1].lower()=='ask': # !!tp ask
                tp_ask(server,info,command)
            elif command[1].lower()=='here': # !!tp here
                tp_here(server,info,command)
            else:
                tellMessage(server,info,"指令输入有误!")
                show_help(server,info)
        else:
            tellMessage(server,info,"指令输入有误!")
            show_help(server,info)
    except Exception as e:
        tellMessage(server,info,"内部错误")
        print(traceback.format_exc())
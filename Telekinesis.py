# -*- coding: utf-8 -*-
import time
import json
import yaml
import os
import nbt
import portalocker
import traceback
from mcdreforged.api.decorator import new_thread
class InvalidCommandError(Exception):
    pass

# 标识性变量，此处的修改不受支持

PLUGIN_METADATA = {
    'name': 'Telekinesis',
    'id': 'telekinesis',
    'version': '1.0.0',
    'description': 'Another Teleportation Plugin for MCDR',
    'author': 'Nyaacinth',
    'link': 'https://github.com/Nyaacinth/Telekinesis',
    'dependencies': {
        'mcdreforged': '>=1.0.0',
        'minecraft_data_api': '>=1.3.0',
        'more_apis': '>=0.1.2'
    }
}

message_prefix = '§d[Telekinesis] §6' # 消息前缀

config_version = 5 # 当前配置文件版本

valid_config_versions = range(1,5+1) # 有效的配置文件版本范围

valid_usergroups = ['guest','user','helper','admin','owner'] # 实用户组

valid_permissions = ['spawn','back','ask_answer','home','home_manage','config','permission_manage'] # 有效的权限

# 默认配置文件的内容
default_config = f'''
config_version: {config_version}
config:
    command_prefix: '!!tp'
    teleport_request_timeout: 30
    teleport_hold_time: 0
    level_location: server/world
    void_protect: true
    player_id_type: uuid
permission:
    guest:
    - spawn
    user:
    - guest
    - back
    - ask_answer
    - home
    - home_manage
    helper:
    - user
    admin:
    - helper
    - config
    owner:
    - all
'''

# 文件处理

def generateDefaultConfig(): # 生成默认配置文件
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'w',encoding='utf8') as f:
        f.write(default_config.lstrip())

def upgradeConfig(server): # 更新配置文件
    _processed = False
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        old_data = yaml.safe_load(f)
        data = yaml.safe_load(default_config)
        data.update(old_data)
        from_config_version = old_data['config_version']
    if from_config_version in range(1, 3+1):
        data['config']['player_id_type'] = 'name'
        _processed = True
    if from_config_version == 4:
        if 'detect_player_by' in old_data['config']:
            del data['config']['detect_player_by']
        data['config']['player_id_type'] = 'name'
        _processed = True
    if _processed == True:
        data['config_version'] = config_version
        server.logger.info(f"Upgrading Configuration ({from_config_version} -> {config_version})")
        with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'w',encoding='utf8') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            yaml.dump(data,f,indent=4,sort_keys=False)

def getConfigKeyList(): # 获取配置键列表
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    return data['config'].keys()

def getConfigKey(keyname): # 读取配置键
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    if keyname in data['config'].keys():
        return data['config'][keyname]
    data = yaml.safe_load(default_config)
    if keyname in data['config'].keys():
        return data['config'][keyname]
    return 'unknown_key'

def updateConfigKey(keyname,value): # 更新配置键
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    default_data = yaml.safe_load(default_config)
    if keyname in default_data['config'].keys():
        if value.isdigit() and isinstance(default_data['config'][keyname],int):
            data['config'][keyname] = int(value)
        elif value.lower() == 'true' and isinstance(default_data['config'][keyname],bool):
            data['config'][keyname] = True
        elif value.lower() == 'false' and isinstance(default_data['config'][keyname],bool):
            data['config'][keyname] = False
        elif isinstance(default_data['config'][keyname],str):
            data['config'][keyname] = value
        else:
            return 'type_error'
        with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'w',encoding='utf8') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            yaml.dump(data,f,indent=4,sort_keys=False)
        return 'succeed'
    return 'unknown_key'

def updatePermissionList(usergroup,permission_list,add=False,remove=False): # 更新权限列表
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        data = yaml.safe_load(f)
    local_valid_permissions = valid_permissions + list(data['permission'].keys()) + ['all']
    if remove is True and not set(permission_list).issubset(set(data['permission'][usergroup])):
        return 'invalid_permissions'
    elif not remove is True and not set(permission_list).issubset(set(local_valid_permissions)):
        return 'invalid_permissions'
    if remove is True and set(permission_list).issubset(set(data['permission'][usergroup])):
        permission_list = list(set(data['permission'][usergroup]) - set(permission_list))
    if not usergroup in data['permission'].keys():
        data['permission'][usergroup] = {}
    if add is True:
        permission_list = data['permission'][usergroup] + permission_list
    data['permission'][usergroup] = list(set(permission_list))
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'w',encoding='utf8') as f:
        yaml.dump(data,f,indent=4,sort_keys=False)
    return 'succeed'

def verifyConfigVersion(): # 验证配置文件版本
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        data = yaml.safe_load(f)
    if data['config_version'] == config_version:
        return True
    return data['config_version']

def getUsergroups(): # 获取存在的用户组
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    return list(data['permission'].keys())

def deleteUsergroup(usergroup): # 删除用户组
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    if usergroup in valid_usergroups:
        return 'in_valid_usergroups'
    if not usergroup in data['permission'].keys():
        return 'unknown_usergroup'
    data['permission'].pop(usergroup)
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'w',encoding='utf8') as f:
        yaml.dump(data,f,indent=4,sort_keys=False)
    return 'succeed'

def getPermissionList(userlevel=None,usergroup=None,recursion=True): # 获取用户组可用权限列表
    if userlevel != None:
        usergroup = valid_usergroups[userlevel]
    with open(f"config/{PLUGIN_METADATA['name']}/config.yaml",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = yaml.safe_load(f)
    if not usergroup in data['permission'].keys():
        return 'invalid_usergroup'
    permission_list = data['permission'][usergroup]
    if recursion is True:
        if 'all' in data['permission'][usergroup]:
            return valid_permissions
        inheritance_usergroups = list(set(data['permission'].keys()).intersection(set(permission_list)))
        if inheritance_usergroups != None:
            for i in range(len(inheritance_usergroups)):
                inheritance_usergroup = inheritance_usergroups[i]
                permission_list.pop(permission_list.index(inheritance_usergroup))
                permission_list.extend(getPermissionList(usergroup=inheritance_usergroup))
    return list(set(permission_list))

def readSpawnPos(): # 读重生点
    nbtData = nbt.nbt.NBTFile(f"{getConfigKey('level_location')}/level.dat",'rb')
    nbtData = nbtData['Data']
    return [nbtData['SpawnX'].value,nbtData['SpawnY'].value,nbtData['SpawnZ'].value]

def readReqList(): # 读请求队列
    with open(f"config/{PLUGIN_METADATA['name']}/requests.json",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = json.load(f)
    return data

def writeReqList(data): # 写请求队列
    with open(f"config/{PLUGIN_METADATA['name']}/requests.json",'w',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        json.dump(data,f)

def readHomeList(): # 读家园传送点列表
    with open(f"config/{PLUGIN_METADATA['name']}/homes.json",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = json.load(f)
    return data

def writeHomeList(data): # 写家园传送点列表
    with open(f"config/{PLUGIN_METADATA['name']}/homes.json",'w',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        data = json.dumps(data,sort_keys=True,indent=4,separators=(',',':'))
        f.write(data)

def readLastTpPosList(): # 读回溯传送队列
    with open(f"config/{PLUGIN_METADATA['name']}/lastPos.json",'r',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        data = json.load(f)
    return data

def writeLastTpPosList(data): # 写回溯传送队列
    with open(f"config/{PLUGIN_METADATA['name']}/lastPos.json",'w',encoding='utf8') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        json.dump(data,f)

# 一般处理

def getPlayerUUID(server,playername): # 获取玩家 UUID
    uuid_int_array = server.get_plugin_instance('minecraft_data_api').get_player_info(playername,'UUID')
    if not uuid_int_array:
        return
    uuid_raw = ''
    for i in uuid_int_array:
        if i < 0:
            i = 4294967296 + i
        uuid_raw = uuid_raw + format(abs(i), 'x')
    uuid = list(uuid_raw)
    uuid.insert(8, '-')
    uuid.insert(13, '-')
    uuid.insert(18, '-')
    uuid.insert(23, '-')
    return ''.join(uuid)

def getPlayerCoordinate(server,player): # 获取玩家坐标（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    coordinate = server.get_plugin_instance('minecraft_data_api').get_player_coordinate(player)
    return coordinate

def getPlayerDimension(server,player): # 获取玩家所处维度（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    dimension = server.get_plugin_instance('minecraft_data_api').get_player_info(player,'Dimension')
    return dimension

def verifyPermission(server,player,permission): # 依赖 getPermissionList() ，验证用户是否具有对应权限
    permission_list = getPermissionList(server.get_permission_level(player))
    if permission in permission_list:
        return True
    return False

def findReqBy(tag,player): # 依赖 readReqList() ，查询是否存在请求
    reqlist = readReqList()
    for tp in reqlist:
        if player == tp[tag]:
            return tp
    return None

def deleteHomePos(server,player,home): # 依赖 readHomeList() ，删除家园传送点
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readHomeList()
    if player in data.keys() and home in data[player].keys():
        data[player].pop(home)
    writeHomeList(data)

def writeHomePos(server,player,home,x,y,z,dimension='minecraft:overworld'): # 依赖 readHomeList() ，设定家园传送点
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readHomeList()
    if not player in data.keys():
        data[player] = {}
    data[player][home] = [x,y,z,dimension]
    writeHomeList(data)

def getHomePos(server,player,home): # 依赖 readHomeList() ，查询是否存在家园传送点
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readHomeList()
    if player in data.keys() and home in data[player].keys():
        return data[player][home]
    return []

def getHomes(server,player): # 依赖 readHomeList() ，获取家园传送点列表
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readHomeList()
    if player in data.keys():
        homes = [ key for key,value in data[player].items() ]
        return homes
    return []

def getLastTpPos(server,player,drop=False): # 依赖 readLastTpPosList() ，查询是否存在可回溯的传送
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readLastTpPosList()
    if player in data:
        pos = data[player]
        if drop == True:
            del data[player]
            writeLastTpPosList(data)
        return pos
    return []

def writeLastTpPos(server,player,x,y,z,dimension='minecraft:overworld'): # 依赖 readLastTpPosList() ，写入可回溯的传送
    if getConfigKey('player_id_type') == 'uuid':
        player = getPlayerUUID(server,player)
    data = readLastTpPosList()
    data[player] = [x,y,z,dimension]
    writeLastTpPosList(data)

def tellMessage(server,to,msg,tell=True,prefix=message_prefix): # 向玩家打印信息
    msg = prefix + msg
    if not tell:
        server.say(msg)
    elif to is not None:
        server.tell(to,msg)

def checkPlayerIfOnline(server,player): # 检查玩家在线情况（由于 MinecraftDataAPI 限制，不可直接在任务执行者线程中使用）
    players = server.get_plugin_instance('minecraft_data_api').get_server_player_list()[2]
    if player in players:
        return True
    return False

def responseTpRequests(to,answer): # 回复传送请求
    reqlist = readReqList()
    for tp in reqlist:
        if to == tp['to']:
            tp['status'] = answer
    writeReqList(reqlist)

def deleteReq(player): # 删除传送请求
    reqlist = readReqList()
    find = -1
    for idx,tp in enumerate(reqlist):
        if player == tp['sendby']:
            find = idx
    if find != -1:
        reqlist.pop(find)
        writeReqList(reqlist)

def createReq(server,sendby,to): # 新增传送请求
    reqlist = readReqList()
    reqlist.append({'sendby':sendby,'to':to,'status':'wait'})
    writeReqList(reqlist)

def handleReq(server,sendby,to): # 处理传送请求
    # 传送请求文字
    timeout = getConfigKey('teleport_request_timeout')
    Prefix = getConfigKey('command_prefix')
    tellMessage(server,sendby,f"已向玩家 {to} 发送传送请求")
    tellMessage(server,to,f"玩家 {sendby} 想传送到你身边")
    tellMessage(server,to,f"在 {timeout} 秒内输入 {Prefix} yes 同意， 输入 {Prefix} no 拒绝")

    # 等待回复
    while timeout > 0:
        req = findReqBy('sendby',sendby)
        if req['status'] == 'wait': # 未回复，继续等待
            time.sleep(1)
            timeout -= 1
        elif req['status'] == 'yes': # 同意
            sec = getConfigKey('teleport_hold_time')
            if sec != 0:
                tellMessage(server,to,f"已同意来自玩家 {sendby} 的传送请求， 将在 {sec} 秒后开始传送")
                tellMessage(server,sendby,f"玩家 {to} 已同意传送请求， 将在 {sec} 秒后传送到玩家 {to} 身边")
            else:
                tellMessage(server,to,f"已同意来自玩家 {sendby} 的传送请求， 正在传送")
                tellMessage(server,sendby,f"玩家 {to} 已同意传送请求， 正在传送")
            while sec > 0:
                time.sleep(1)
                sec -= 1
            coordinate = getPlayerCoordinate(server,player=sendby)
            dimension = getPlayerDimension(server,player=sendby)
            writeLastTpPos(server,sendby,coordinate.x,coordinate.y,coordinate.z,dimension)
            server.execute(f"tp {sendby} {to}")
            break
        elif req['status'] == 'no': # 不同意
            tellMessage(server,to,f"已拒绝来自玩家 {sendby} 的传送请求， 取消传送")
            tellMessage(server,sendby,f"{to} 拒绝了传送请求")
            break

    # 请求等待超时
    if timeout == 0 and getConfigKey('teleport_request_timeout') != 0:
        tellMessage(server,to,f"来自玩家 {sendby} 的传送请求已超时")
        tellMessage(server,sendby,f"玩家 {to} 超时未回复， 传送请求已被系统取消")

    # 删除传送请求
    deleteReq(sendby)

# 指令

def show_help(server,info): # 插件帮助，展示可用子命令
    Prefix = getConfigKey('command_prefix')
    helpmsg = f'''
    {Prefix} spawn - 传送到世界重生点
    {Prefix} back - 进行回溯传送
    {Prefix} ask <玩家> - 请求传送自己到 <玩家> 身边
    {Prefix} <yes|no> - 同意/拒绝传送到自己身边的请求
    {Prefix} sethome [传送点名称] [--replace] - 设置家园传送点
    {Prefix} home [传送点名称] - 传送到家园
    {Prefix} homes - 查看已设置的家园传送点
    {Prefix} delhome [传送点名称] - 删除家园传送点
    {Prefix} config <键>|--list <值> - 更新/查看设置键
    {Prefix} permission <query|add|set|remove> [用户组] [权限名|用户组名]
      - 更新/查询/删除用户组权限、修改用户组间继承关系或删除虚用户组
    {Prefix} help - 展示本帮助信息
    {Prefix} about - 关于
    '''
    tellMessage(server,info.player,'帮助信息\n'+helpmsg)

def show_about(server,info): # 展示插件关于信息
    aboutmsg = f'''
    当前版本： v{PLUGIN_METADATA['version']}

    一个小小的传送插件， 维护者： {PLUGIN_METADATA['author']}
    在此致谢 dream-rhythm ， 本插件以 tpHelper 为工作基础重写而来
    '''
    tellMessage(server,info.player,'关于信息\n'+aboutmsg)

def tp_config(server,info,command,command_length): # !!tp config
    permission = 'config'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    if command_length == 3:
        if command[2].lower() == '--list':
            tellMessage(server,info.player,f"存在以下有效的设置键：\n\n    {' '.join(getConfigKeyList())}\n")
            return
        result = getConfigKey(command[2])
        if result == 'unknown_key':
            tellMessage(server,info.player,f"无法获取到值， 无效的键 {command[2]}")
            return
        tellMessage(server,info.player,f"设置键 {command[2]} 的值现在为 {result}")
        return
    elif command[3] != None:
        status = updateConfigKey(command[2],command[3])
        if status == 'unknown_key':
            tellMessage(server,info.player,f"更新设置失败， 无效的键 {command[2]}")
            return
        if status == 'type_error':
            tellMessage(server,info.player,f"更新设置失败， 键 {command[2]} 的值类型不正确")
            return
        tellMessage(server,info.player,f"设置键 {command[2]} 的值现在为 {command[3]}")

def tp_permission(server,info,command,command_length): # !!tp permission
    permission = 'permission_manage'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    if command_length == 3 and command[2].lower() == 'query':
        custom_usergroups = list(set(getUsergroups()) - set(valid_usergroups))
        if custom_usergroups == []:
            tellMessage(server,info.player,f"查询存在的用户组\n\n当前存在以下实用户组：\n\n    {' '.join(valid_usergroups)}\n\n且不存在虚用户组\n")
            return
        tellMessage(server,info.player,f"查询存在的用户组\n\n当前存在以下实用户组：\n\n    {' '.join(valid_usergroups)}\n\n与以下虚用户组：\n\n    {' '.join(custom_usergroups)}\n")
        return
    elif command_length == 4 and command[2].lower() == 'remove':
        status = deleteUsergroup(usergroup=command[3])
        if status == 'unknown_usergroup':
            tellMessage(server,info.player,f"无法删除用户组 {command[3]} ， 因为其不存在")
            return
        elif status == 'in_valid_usergroups':
            tellMessage(server,info.player,f"无法删除用户组 {command[3]} ， 因其为实用户组")
            return
        tellMessage(server,info.player,f"虚用户组 {command[3]} 已被删除")
    permission_list = getPermissionList(userlevel=None,usergroup=command[3],recursion=False)
    if command_length == 4 and command[2].lower() == 'query':
        if permission_list == []:
            tellMessage(server,info.player,f"用户组 {command[3]} 现在没有任何权限")
            return
        tellMessage(server,info.player,f"用户组 {command[3]} 具有以下权限：\n\n    {' '.join(permission_list)}\n")
    elif command_length >= 5 and command[2].lower() == 'add':
        status = updatePermissionList(usergroup=command[3],permission_list=command[4::],add=True)
        if status == 'invalid_permissions':
            tellMessage(server,info.player,'更新权限失败， 参数中存在无效的权限')
            return
        tellMessage(server,info.player,f"用户组 {command[3]} 现有权限 {' '.join(getPermissionList(userlevel=None,usergroup=command[3],recursion=False))}")
    elif command_length >= 5 and command[2].lower() == 'set':
        status = updatePermissionList(usergroup=command[3],permission_list=command[4::],add=False)
        if status == 'invalid_permissions':
            tellMessage(server,info.player,'更新权限失败， 参数中存在无效的权限')
            return
        tellMessage(server,info.player,f"用户组 {command[3]} 现有权限 {' '.join(getPermissionList(userlevel=None,usergroup=command[3],recursion=False))}")
    elif command_length >= 5 and command[2].lower() == 'remove':
        status = updatePermissionList(usergroup=command[3],permission_list=command[4::],add=False,remove=True)
        if status == 'invalid_permissions':
            tellMessage(server,info.player,'更新权限失败， 参数中存在无效的权限')
            return
        permission_list = getPermissionList(userlevel=None,usergroup=command[3],recursion=False)
        if permission_list == []:
            tellMessage(server,info.player,f"用户组 {command[3]} 现在没有任何权限")
            return
        tellMessage(server,info.player,f"用户组 {command[3]} 现有权限 {' '.join(permission_list)}")

@new_thread # 原因：间接引用了 MinecraftDataAPI（getPlayerCoordinate/getPlayerDimension）
def tp_spawn(server,info): # !!tp spawn
    permission = 'spawn'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    pos = readSpawnPos()
    sec = getConfigKey('teleport_hold_time')
    if sec != 0:
        tellMessage(server,info.player,f"系统已收到指令， 将在 {sec} 秒后传送到世界重生点")
    while sec > 0:
        time.sleep(1)
        sec -= 1
    tellMessage(server,info.player,"传送到世界重生点")
    coordinate = getPlayerCoordinate(server,player=info.player)
    dimension = getPlayerDimension(server,player=info.player)
    writeLastTpPos(server,info.player,coordinate.x,coordinate.y,coordinate.z,dimension)
    server.execute(f"execute in minecraft:overworld run tp {info.player} {pos[0]} {pos[1]} {pos[2]}")

@new_thread # 原因：间接引用了 MinecraftDataAPI（getPlayerCoordinate/getPlayerDimension）
def tp_sethome(server,info,command=None,replace=False): # !!tp sethome
    permission = 'home_manage'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    if command != None and command[2] != None:
        home=command[2].lower()
    else:
        home='home'
    if getHomePos(server,info.player,home) == [] or replace == True:
        coordinate = getPlayerCoordinate(server,player=info.player)
        dimension = getPlayerDimension(server,player=info.player)
        tellMessage(server,info.player,f"设置家园传送点 {home}")
        writeHomePos(server,info.player,home,coordinate.x,coordinate.y,coordinate.z,dimension)
    else:
        tellMessage(server,info.player,f"已存在家园传送点 {home} ， 若要覆盖请先删除或增加参数 --replace")

@new_thread # 原因：间接引用了 MinecraftDataAPI（getPlayerCoordinate/getPlayerDimension）
def tp_home(server,info,command=None): # !!tp home
    permission = 'home'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    sec = getConfigKey('teleport_hold_time')
    if command != None and command[2] != None:
        home=command[2].lower()
    else:
        home='home'
    pos = getHomePos(server,info.player,home)
    if pos != []:
        if sec != 0:
            tellMessage(server,info.player,f"系统已收到指令， 将在 {sec} 秒后传送到家园 {home}")
        while sec > 0:
            time.sleep(1)
            sec -= 1
        tellMessage(server,info.player,f"正在传送到家园 {home}")
        coordinate = getPlayerCoordinate(server,player=info.player)
        dimension = getPlayerDimension(server,player=info.player)
        writeLastTpPos(server,info.player,coordinate.x,coordinate.y,coordinate.z,dimension)
        server.execute(f"execute in {pos[3]} run tp {info.player} {pos[0]} {pos[1]} {pos[2]}")
    else:
        tellMessage(server,info.player,f"家园传送点 {home} 不存在， 请先创建一个")

def tp_delhome(server,info,command=None): # !!tp delhome
    permission = 'home_manage'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    if command != None and command[2] != None:
        home=command[2].lower()
    else:
        home='home'
    homes = getHomes(server,info.player)
    if home in homes:
        tellMessage(server,info.player,f"正在删除家园传送点 {home}")
        deleteHomePos(server,info.player,home)
    else:
        tellMessage(server,info.player,f"家园传送点 {home} 不存在")

def tp_homes(server,info): # !!tp homes
    permission = 'home'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    Prefix = getConfigKey('command_prefix')
    homes = ' '.join(getHomes(server,info.player))
    if homes != '':
        tellMessage(server,info.player,f"您设置的家园传送点有：\n\n    {homes}\n")
    else:
        tellMessage(server,info.player,f"您还没有设置过家园传送点， 可以使用 {Prefix} sethome 设定一个")

def tp_yesno(server,info,command): # !!tp yes/no
    permission = 'ask_answer'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    req = findReqBy('to',info.player)
    if req == None:
        tellMessage(server,info.player,'目前没有待确认的请求')
    else:
        responseTpRequests(info.player,command[1].lower())

@new_thread # 原因：间接引用了 MinecraftDataAPI（getPlayerCoordinate/getPlayerDimension）
def tp_back(server,info): # !! tp back
    permission = 'back'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    sec = getConfigKey('teleport_hold_time')
    pos = getLastTpPos(server,info.player)
    if pos != []:
        if sec != 0:
            tellMessage(server,info.player,f"系统已收到指令， 将在 {sec} 秒后回溯传送")
        while sec > 0:
            time.sleep(1)
            sec -= 1
        tellMessage(server,info.player,'正在进行回溯传送')
        if getConfigKey('void_protect') is True and pos[1] < 1:
            tellMessage(server,info.player,f"无法执行操作， 目标已在虚空中 (x={round(pos[0],2)} y={round(pos[1],2)} z={round(pos[2],2)})")
            return
        pos = getLastTpPos(server,info.player,True)
        coordinate = getPlayerCoordinate(server,player=info.player)
        dimension = getPlayerDimension(server,player=info.player)
        writeLastTpPos(server,info.player,coordinate.x,coordinate.y,coordinate.z,dimension)
        server.execute(f"execute in {pos[3]} run tp {info.player} {pos[0]} {pos[1]} {pos[2]}")
    else:
        tellMessage(server,info.player,'您没有可回溯的传送')

@new_thread # 原因：间接引用了 MinecraftDataAPI（checkPlayerIfOnline）与长耗时函数 handleReq()
def tp_ask(server,info,command): # !! tp ask <playername>
    permission = 'ask_answer'
    if not verifyPermission(server,info.player,permission):
        tellMessage(server,info.player,f"无法执行操作， 因为缺少 {permission} 权限，如果您确信这不应发生请联系管理员")
        return
    if checkPlayerIfOnline(server,command[2]) == False:
        tellMessage(server,info.player,'请求失败， 指定的玩家不存在或未上线')
    elif findReqBy('sendby',info.player):
        tellMessage(server,info.player,'请求失败， 请先处理现存的传送请求')
    elif findReqBy('to',command[1]):
        tellMessage(server,info.player,'请求失败， 对方仍有待处理传送请求')
    else:
        createReq(server,info.player,command[2])
        handleReq(server,info.player,command[2])

@new_thread
def death_handle(server,playername):
    coordinate = getPlayerCoordinate(server,playername)
    dimension = getPlayerDimension(server,playername)
    tellMessage(server,playername,f"您的死亡地点：\n    x = {round(coordinate.x,2)}, y = {round(coordinate.y,2)}, z = {round(coordinate.z,2)}, dim = {dimension}")
    writeLastTpPos(server,playername,coordinate.x,coordinate.y,coordinate.z,dimension)
    tellMessage(server,playername,'可以使用 !!tp back 返回死亡地点')

# 外部事件处理

def on_load(server,prev): # 插件初始化
    if not os.path.exists(f"config/{PLUGIN_METADATA['name']}"):
        os.mkdir(f"config/{PLUGIN_METADATA['name']}")
    if not os.path.exists(f"config/{PLUGIN_METADATA['name']}/config.yaml"):
        server.logger.info(f"Generating Default Configuration, Thanks for Using {PLUGIN_METADATA['name']}!")
        generateDefaultConfig()
    if verifyConfigVersion() != True and verifyConfigVersion() in valid_config_versions:
        upgradeConfig(server)
    elif verifyConfigVersion() != True:
        server.unload_plugin(PLUGIN_METADATA['id'])
        raise RuntimeError('Invalid Configuration Version, Please Do Not Downgrade')
    Prefix = getConfigKey('command_prefix')
    if not os.path.exists(f"config/{PLUGIN_METADATA['name']}/homes.json"):
        writeHomeList({})
    if not os.path.exists(f"config/{PLUGIN_METADATA['name']}/lastPos.json"):
        writeLastTpPosList({})
    writeReqList([])
    server.register_help_message(f"{Prefix} help",f"显示 {PLUGIN_METADATA['name']} 帮助")
    server.register_event_listener('more_apis.death_message', on_death_message)

def on_death_message(server,death_message):
    playername = death_message.split()[0]
    death_handle(server,playername)    

def on_user_info(server,info): # 接收输入
    Prefix = getConfigKey('command_prefix')
    command = info.content.split()
    if len(command) == 0 or command[0] != Prefix:
        return
    info.cancel_send_to_server()
    if info.is_from_console:
        server.logger.warn(f"Sorry, currently use {PLUGIN_METADATA['name']} in console is not allowed, please use a client instead")
        return
    command_length = len(command)
    try:
        if command_length == 1: # !!tp
            show_help(server,info)
        elif command_length == 2: # !!tp help/about/yes/no/back/home/homes/sethome/delhome
            if command[1].lower() == 'help': # !!tp help
                show_help(server,info)
            elif command[1].lower() == 'about': # !!tp about
                show_about(server,info)
            elif command[1].lower() == 'spawn': # !!tp spawn
                tp_spawn(server,info)
            elif command[1].lower() in ['yes','no']: # !!tp yes/no
                tp_yesno(server,info,command)
            elif command[1].lower() == 'back': # !!tp back
                tp_back(server,info)
            elif command[1].lower() == 'home': # !!tp home
                tp_home(server,info)
            elif command[1].lower() == 'homes': # !!tp homes
                tp_homes(server,info)
            elif command[1].lower() == 'sethome': # !!tp sethome
                tp_sethome(server,info)
            elif command[1].lower() == 'delhome': # !!tp delhome
                tp_delhome(server,info)
            else:
                raise InvalidCommandError
        elif command_length == 3: # !!tp ask/home/sethome/delhome/config/permission
            if command[1].lower() == 'ask': # !!tp ask <playername>
                tp_ask(server,info,command)
            elif command[1].lower() == 'home': # !!tp home <home>
                tp_home(server,info,command)
            elif command[1].lower() == 'sethome': # !!tp sethome <home> or !!tp sethome --replace
                if command[2].lower() == '--replace':
                    tp_sethome(server,info,command=None,replace=True)
                else:
                    tp_sethome(server,info,command)
            elif command[1].lower() == 'delhome': # !!tp delhome <home>
                tp_delhome(server,info,command)
            elif command[1].lower() == 'config': # !!tp config <key>|--list
                tp_config(server,info,command,command_length)
            elif command[1].lower() == 'permission' and command[2].lower() == 'query': # !!tp permission query <usergroup>
                tp_permission(server,info,command,command_length)
            else:
                raise InvalidCommandError
        elif command_length == 4: # !!tp sethome/config/permission
            if command[1].lower() == 'sethome' and command[3].lower() == '--replace': # !!tp sethome <home> --replace
                tp_sethome(server,info,command,replace=True)
            elif command[1].lower() == 'config': # !!tp config <key> <value>
                tp_config(server,info,command,command_length)
            elif command[1].lower() == 'permission' and command[2].lower() in ['query','remove']: # !!tp permission <query|remove> <usergroup> [...]
                tp_permission(server,info,command,command_length)
            else:
                raise InvalidCommandError
        elif command_length >= 5: # !!tp permission
            if command[1].lower() == 'permission' and command[2].lower() in ['add','set','remove']: # !!tp permission <add|set|remove> <usergroup> ...
                tp_permission(server,info,command,command_length)
            else:
                raise InvalidCommandError
        else:
            raise InvalidCommandError
    except InvalidCommandError:
        tellMessage(server,info.player,'指令输入有误!')
        show_help(server,info)
    except:
        tellMessage(server,info.player,'插件运行时出现了异常， 相关错误信息请检查控制台',tell=False)
        print(traceback.format_exc())

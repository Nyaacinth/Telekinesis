## Telekinesis

Another MCDR Teleportation Plugin inspired by tpHelper, currently only support Chinese.

If you need English support, please open an issue and let me know about that, maybe I will do it later.

一个小小的传送插件，受 dream-rhythm 的 tpHelper 启发而做，提供传送相关功能支持

### 功能

<kbd>!!tp back</kbd> 进行回溯传送

<kbd>!!tp spawn</kbd> 传送到世界重生点

<kbd>!!tp ask \<玩家></kbd> 请求传送自己到 \<玩家> 身边

<kbd>!!tp \<yes/no></kbd> 同意/拒绝传送到自己身边的请求

<kbd>!!tp sethome \<传送点名称></kbd> 设置家园传送点

<kbd>!!tp home \<传送点名称></kbd> 传送到家园

<kbd>!!tp homes</kbd> 查看已设置的家园传送点

<kbd>!!tp delhome \<传送点名称></kbd> 删除家园传送点

<kbd>!!tp help</kbd> 查看帮助信息

<kbd>!!tp about</kbd> 查看关于

### 配置文件

配置文件默认会生成于 MCDR 工作目录下的 config/Telekinesis/config.yaml ，目前存在以下内容：

|键名|默认值|含义|
|----|----|----|
|`config_version`|`1`|配置文件版本，请勿修改|
|`command_prefix`|`'!!tp'`|指令前缀|
|`level_location`|`server/world`|level.dat 所在目录，用于检测出生点|
|`teleport_hold_time`|`0`|传送执行前等待的时间（单位：秒）|
|`teleport_request_timeout`|`30`|传送请求超时的时间（单位：秒）|

### 依赖

[nbt](https://pypi.org/project/NBT)：用于读取存档获取出生点

[PyYAML](https://pypi.org/project/PyYAML)：配置文件

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI)：引用 API

### Todo

- [x] 原 tpHelper 的关键功能（请求传送 & 回溯传送）
- [x] 支持 tp/set/del home 功能
- [ ] 支持玩家死亡的回溯传送（暂无法实现，参见 [Migrate from MCDR 0.x](https://mcdreforged.readthedocs.io/en/latest/migrate_from_0.x.html#compatibility) ）
- [ ] 消耗经验的传送
- [x] 类 Essentials 的延时传送
- [ ] 支持权限管理

喵！

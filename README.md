## Telekinesis

Another MCDR Teleportation Plugin inspired by tpHelper, currently only support Chinese.

If you need English support, please open an issue and let me know about that, maybe I will do it later.

一个小小的传送插件，受 dream-rhythm 的 tpHelper 启发而做，提供传送相关功能支持

### 功能

<kbd>!!tp back</kbd> 进行回溯传送

<kbd>!!tp spawn</kbd> 传送到世界重生点

<kbd>!!tp ask \<玩家></kbd> 请求传送自己到 \<玩家> 身边

<kbd>!!tp \<yes|no></kbd> 同意/拒绝传送到自己身边的请求

<kbd>!!tp sethome [传送点名称] [--replace]</kbd> 设置家园传送点

<kbd>!!tp home [传送点名称]</kbd> 传送到家园

<kbd>!!tp homes</kbd> 查看已设置的家园传送点

<kbd>!!tp delhome [传送点名称]</kbd> 删除家园传送点

<kbd>!!tp config \<键>|--list \<值></kbd> 查看/更新设置或列出设置键

<kbd>!!tp permission \<query|add|set|remove> [用户组] [权限名|用户组名]</kbd>

- 更新/查询/删除用户组权限、修改用户组间继承关系或删除虚用户组

- 总之是与权限管理相关的

<kbd>!!tp help</kbd> 查看帮助信息

<kbd>!!tp about</kbd> 查看关于

### 配置文件

配置文件默认会生成于 MCDR 工作目录下的 config/Telekinesis/config.yaml ，目前存在以下内容：

#### 基础配置

提示：你也可以在游戏内使用 `!!tp config <键> <值>` 来更新设置，更新的设置将立即生效

|键名|默认值|数据类型|含义|
|----|----|----|----|
|`config_version`|`4`|整型|配置文件版本，请勿修改|
|`command_prefix`|`!!tp`|字符串|指令前缀|
|`level_location`|`server/world`|字符串|level.dat 所在目录，用于检测出生点|
|`teleport_hold_time`|`0`|整型|传送执行前等待的时间（单位：秒）|
|`teleport_request_timeout`|`30`|整型|传送请求超时的时间，设为 0 永不超时（单位：秒）|
|`void_protect`|`true`|布尔值|是否防止玩家 back 时落入虚空|
|`player_id_type`|`uuid`<sup>[1]</sup>|字符串|玩家辨识依据（ `uuid` 或 `name` ）

[1]： 若从配置文件版本 4 及以下的版本升级则自动设为 `name` 以维持兼容性

#### 权限配置

依照 [MCDR 相关文档](https://mcdreforged.readthedocs.io/zh_CN/latest/permission.html)，玩家在 MCDR 中的权限分为 0~4 五个等级，即 guest, user, helper, admin, owner 五个用户组

Telekinesis 直接使用对应用户组作为键名，并存在以下权限：

|权限名|相关指令|
|----|----|
|`spawn`|`!!tp spawn`|
|`back`|`!!tp back`|
|`ask_answer`|`!!tp ask <玩家名>`</br>`!!tp <yes\|no>`|
|`home`|`!!tp home`|
|`home_manage`|`!!tp sethome [传送点名称] [--replace]`</br>`!!tp delhome [传送点名称]`|
|`config`|`!!tp config <键>\|--list <值>`|
|`permission_manage`|`!!tp permission ...`|

默认情况下权限分配如下：

|用户组|权限|
|----|----|
|guest|`spawn`|
|user|`back`</br>`ask_answer`</br>`home`</br>`home_manage`</br>+ guest 用户组的权限|
|helper|user 用户组的权限|
|admin|`config`</br>+ helper 用户组的权限|
|owner|所有权限|

用户组键下的权限直接以列表形式写出，如有需求修改即可

您也可以使用 `!!tp permission ...` 指令在游戏内修改权限，修改将立即生效

- 文件特殊说明：
    - 若在权限列表中写入另一用户组的名称，将直接继承其权限
    - 要使某一权限组不具备任何权限，请将其值设为空列表（eg. `guest: []`）
    - 权限列表中填入 `all` 代表赋予该用户组和所有继承它的组所有权限

### 依赖

[MCDReforged](https://github.com/Fallen-Breath/MCDReforged) (>=1.0.0)：一切的源头

[NBT](https://pypi.org/project/NBT)：用于读取存档获取出生点

[PyYAML](https://pypi.org/project/PyYAML)：配置文件

[portalocker](https://pypi.org/project/portalocker)：跨平台文件锁

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI) (>=1.3.0)：引用 API

[MoreAPIs](https://github.com/HuajiMUR233/MoreAPIs) (>=0.1.2)：引用 API

### Features

- [x] 原 tpHelper 的关键功能（请求传送 & 回溯传送）
- [x] 支持 tp/set/del home 功能
- [x] 支持玩家死亡的回溯传送
- [x] 基于 UUID 辨识玩家
- [x] 类 Essentials 的延时传送
- [x] 支持权限管理
- [ ] 多语言支持

喵？喵喵喵喵！！

## Telekinesis

一个小小的传送插件，修改自 dream-rhythm 的 tpHelper ，变更了部分实现以求在高版本 MCDR 上正常运行。

### 功能

<kbd>!!tp back</kbd> 进行回溯传送

<kbd>!!tp spawn</kbd> 传送到世界重生点

<kbd>!!tp \<玩家></kbd> 请求传送自己到 \<玩家> 身边

<kbd>!!tp \<yes/no></kbd> 同意/拒绝传送到自己身边的请求

### 依赖

[nbt](https://pypi.org/project/NBT)（Python 库）：用于读取存档获取出生点

[OnlinePlayerAPI](https://github.com/zhang-anzhi/MCDReforgedPlugins/tree/master/OnlinePlayerAPI)（MCDR 插件）：引用 API

### To-do

- [ ] 支持 home 与 sethome 功能，并尝试直接复用来自 Essentials 插件的数据
- [ ] 支持玩家死亡的回溯传送

\>ωo

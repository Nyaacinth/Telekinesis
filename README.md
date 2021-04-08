## Telekinesis

一个小小的传送插件，源于 dream-rhythm 的 tpHelper ，现正重写中。

现阶段功能已完全可以替代 v0.0.2-alpha，若有需求请直接下载仓库中的版本使用

### 功能

<kbd>!!tp back</kbd> 进行回溯传送

<kbd>!!tp spawn</kbd> 传送到世界重生点

<kbd>!!tp ask \<玩家></kbd> 请求传送自己到 \<玩家> 身边

<kbd>!!tp \<yes/no></kbd> 同意/拒绝传送到自己身边的请求

### 依赖

[nbt](https://pypi.org/project/NBT)：用于读取存档获取出生点

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI)：引用 API

### Todo

- [x] 原 tpHelper 的关键功能（请求传送 & 回溯传送）
- [ ] 支持 tp/set/del home 功能，并尝试直接复用来自 Essentials 插件的数据
- [ ] 支持玩家死亡的回溯传送（暂无法实现，参见 [Migrate from MCDR 0.x](https://mcdreforged.readthedocs.io/en/latest/migrate_from_0.x.html#compatibility) ）
- [ ] 消耗经验的传送
- [x] 类 Essentials 的延时传送
- [ ] 支持权限管理

\>ωo

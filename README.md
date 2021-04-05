## Telekinesis

一个小小的传送插件，源于 dream-rhythm 的 tpHelper ，现正重写中。

可用且功能齐全的版本存在于已发布的 v0.0.2-alpha ，请移步 [release](https://github.com/Nyaacinth/Telekinesis/releases/tag/b8a0cb8) 查看

### 功能

<kbd>!!tp back</kbd> 进行回溯传送

<kbd>!!tp spawn</kbd> 传送到世界重生点

~~<kbd>!!tp \<玩家></kbd> 请求传送自己到 \<玩家> 身边~~（重写中）

~~<kbd>!!tp \<yes/no></kbd> 同意/拒绝传送到自己身边的请求~~（重写中）

### 依赖

[nbt](https://pypi.org/project/NBT)：用于读取存档获取出生点

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI)：引用 API

### Todo

- [ ] 支持 tp/set/del home 功能，并尝试直接复用来自 Essentials 插件的数据
- [ ] 支持玩家死亡的回溯传送（暂无法实现，参见 [Migrate from MCDR 0.x](https://mcdreforged.readthedocs.io/en/latest/migrate_from_0.x.html#compatibility) ）
- [ ] 以 UUID 区分不同玩家
- [ ] 消耗经验的传送
- [ ] 类 Essentials 的延时传送
- [ ] 支持权限管理

\>ωo

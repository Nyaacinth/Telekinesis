def getPlayerUUID(server, playername): # 获取玩家 UUID
    uuid_int_array = server.get_plugin_instance("minecraft_data_api").get_player_info(playername,"UUID")
    if not uuid_int_array:
        return
    uuid_raw = ""
    for node in uuid_int_array:
        if node < 0:
            node = 4294967296 + node
        uuid_raw = uuid_raw + format(abs(node), "x")
    uuid_array = list(uuid_raw)
    for loc in [8, 13, 18, 23]
        uuid_array.insert(loc, "-")
    return "".join(uuid_array)

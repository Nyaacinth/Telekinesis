from . import utils, message_handler as messageHandler

@new_thread("Telekinesis_Info_Handler")
def on_info(server, info):
    if info.is_user:
        return
    playername = messageHandler.handleDeathMessage(server, info.content)
    if playername:
        pass # TODO

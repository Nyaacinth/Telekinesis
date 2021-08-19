def handleDeathMessage(server, message):
    with server.open_bundled_file("data/death_messages.yaml") as f:
        regexes = yaml.safe_load(f)
    for regex in regexes:
        if re.fullmatch(regex, message):
            return message.split()[0]
    return False

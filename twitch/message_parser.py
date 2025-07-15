import datetime

def parse_privmsg(raw_message: str):
    if "PRIVMSG" in raw_message:
        try:
            prefix, trailing = raw_message.split(" :", 1)
            user = prefix.split("!")[0][1:]
            channel = prefix.split(" PRIVMSG ")[-1].split(" :")[0].strip()
            content = trailing.strip()
            return {
                "user": user,
                "channel": channel,
                "message": content,
                "timestamp": datetime.datetime.utcnow()
            }
        except Exception as e:
            print(f"[Parser Error] {e}")
    return None

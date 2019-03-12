# Errors


def error_command():
    return "Command not found! Type !help for help!"


def error_param(cmd, error):
    return error + "For the correct syntax type [!help " + str(cmd) + "]"


def error_time():
    return "Time syntax error. Type {!help tod]"


def error_merb_not_found():
    return "Merb not found. For a list of named mobs type [!merbs]"

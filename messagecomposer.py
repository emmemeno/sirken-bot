import timehandler as timeh


# Fancy compose and format output functions

def prettify(text: str, my_type="BLOCK", pre_content=""):

    prefix = ""
    postfix = prefix

    if my_type == "BLOCK":
        prefix = "```\n"
        postfix = prefix

    elif my_type == "CSS":
        prefix = "```css\n"
        postfix = "```\n"

    elif my_type == "SINGLE":
        prefix = "`\n"
        postfix = prefix

    return pre_content + prefix + text + postfix


def time_remaining(name, eta, plus_minus, window, spawns, accuracy):
    now = timeh.now()
    eta = timeh.change_tz(eta, "UTC")
    postfix = ""
    prefix = ""
    output = "[" + name + "] "
    approx = ""
    if accuracy <= 0 or spawns > 6:
        approx = ".roughly"
        if accuracy <= -1 or spawns >= 10:
            approx = ".very_roughly"

    if now > eta and not plus_minus:
        output += "ToD too old. Please update it if you have a chance! "
    if now > eta and plus_minus:
        output += "window is close. Please update its ToD if u have a chance! "
    if now < eta and not plus_minus:
        output += "will %s spawn in %s" % (approx, timeh.countdown(now, eta))
    if now < window['start'] and plus_minus:
        output += "window will %s open in %s" % (approx, timeh.countdown(now, eta))
    if window['start'] <= now <= window['end']:
        prefix = "# "
        postfix = "<-"
        output += "in window until %s " % timeh.countdown(now, eta)
    # output += " - {ToD: %s} signed by %s" % (tod.strftime(DATE_FORMAT_PRINT), author)
    return prefix + output + postfix + "\n"


def detail(name, tod, pop, signed, respawn_time, plus_minus, window_start, window_end, accuracy, eta):
    output = "%s\n" % name
    output += "=" * len(name) + "\n\n"
    approx = ""
    if accuracy == 0:
        approx = ".roughly "

    output += " {LAST POP}     [%s]\n" \
              " {LAST TOD}     [%s]\n" \
              " {RESPAWN TIME} [%s±%s]\n" \
              " {WINDOW OPEN}  [%s]\n" \
              " {WINDOW CLOSE} [%s]\n" \
              " {SIGNED BY}    [%s] %s\n" \
              " {ETA}          [%s]\n" % \
              (pop, tod, respawn_time, plus_minus, window_start, window_end, signed, approx, eta)
    return output


def alias(name, merb_alias):
    output = "[%s] " % name
    for alt in merb_alias:
        output += "{%s} " % alt
    output += "\n"
    return output

import timehandler as timeh
import config


def message_cut(input_text: str, limit: int):
    """
    Function that take a string as argument and breaks it in smaller chunks
    :param input_text: str
    :param limit: int
    :return: output: list()
    """

    output = list()

    while len(input_text) > limit:

        # find a smart new limit based on newline...
        smart_limit = input_text[0:limit].rfind('\n') + 1
        if smart_limit == -1:
            # ...or find a smart new limit based on blank space
            smart_limit = input_text[0:limit].rfind(' ') + 1
        output.append(input_text[0:smart_limit])
        input_text = input_text[smart_limit:]

    output.append(input_text)
    return output


def prettify(text: str, my_type="BLOCK"):

    output_text = list()
    prefix = postfix = ""
    cut_text = message_cut(text, config.MAX_MESSAGE_LENGTH)

    for chunk in cut_text:
        if my_type == "BLOCK":
            prefix = postfix = "```\n"
        elif my_type == "CSS":
            prefix = "```css\n"
            postfix = "```\n"

        elif my_type == "SINGLE":
            prefix = "`\n"
            postfix = prefix
        output_text.append(prefix + chunk + postfix)

    return output_text


def time_remaining(name, eta, plus_minus, window, spawns, accuracy, target):
    now = timeh.now()
    postfix = ""
    prefix = ""
    output = "[" + name + "] "
    approx = ""
    if accuracy <= 0:
        approx = "{roughly} "
    if accuracy <= -1 or spawns >= 1:
        approx = "{very roughly} "
    if not plus_minus:
        if now > eta:
            output += "ToD too old. Please update it if you have a chance! "
        else:
            output += "will %sspawn in %s " % (approx, timeh.countdown(now, eta))
    else:
        if now > window['end']:
            output += "window is close. Please update ToD! "
        elif now < window['start']:
            output += "window will %sopen in %s " % (approx, timeh.countdown(now, eta))
        elif window['start'] <= now <= window['end']:
            prefix = ""
            postfix = "## "
            output += "is %sin window until %s " % (approx, timeh.countdown(now, eta))

    if spawns >= 1:
        output += "(%s respawns since last update) " % spawns
    if target:
        postfix += ".target"
    return prefix + output + postfix + "\n"


def detail(name, tod, pop, signed_tod, signed_pop, respawn_time, plus_minus, tags, window_start, window_end, accuracy, eta):
    output = "%s\n" % name
    output += "=" * len(name) + "\n\n"
    approx = ""
    if accuracy == 0:
        approx = "'roughly' "
    print_tags = ""
    for tag in tags:
        print_tags += "%s " % tag
    if print_tags:
        print_tags = print_tags[:-1]

    output += "{LAST POP}      [%s]\n" \
              "{LAST TOD}      [%s]\n" \
              "{RESPAWN TIME}  [%s±%s]\n" \
              "{TAGS}          [%s]\n" \
              % (pop, tod, respawn_time, plus_minus, print_tags)
    if plus_minus:
        output += "{WINDOW OPEN}   [%s]\n" \
                  "{WINDOW CLOSE}  [%s]\n" \
                  % (window_start, window_end)

    output += "{SIGNED TOD BY} [%s] %s\n" \
              "{SIGNED POP BY} [%s]\n" \
              "{ETA}           [%s]\n" \
              % (simple_username(signed_tod), approx, simple_username(signed_pop), eta)
    return output


def output_list(content: list):
        output = ""
        for line in content:
            output += line
        if output == "":
            output = "Empty! :("
        return output


def meta(name, merb_alias, merb_tag):
    output = "[%s] " % name
    for alt in merb_alias:
        output += "{%s} " % alt
    for tag in merb_tag:
        output += "#%s " % tag
    output += "\n"
    return output


def alias(name, merb_alias):
    output = "[%s] " % name
    for alt in merb_alias:
        output += "{%s} " % alt
    output += "\n"
    return output


def simple_username(user: str):
    new_user = user.split("#")
    if new_user:
        return new_user[0]
    else:
        return user

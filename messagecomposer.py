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


def time_remaining(name, eta, plus_minus, window, spawns, accuracy, target, snippet):
    now = timeh.now()
    postfix = ""
    prefix = ""
    output = "[" + name + "] "
    approx = ""
    if accuracy <= 0 or spawns == 1:
        approx = "{roughly} "
    if accuracy <= -1 or spawns > 1:
        approx = "{very roughly} "
    if not plus_minus:
        if now > eta:
            output += "ToD is too old. "
        else:
            output += "will %sspawn in %s " % (approx, timeh.countdown(now, eta))
    else:
        if now > window['end']:
            output += "window is closed "
        elif now < window['start']:
            output += "window will %sopen in %s " % (approx, timeh.countdown(now, eta))
        elif window['start'] <= now <= window['end']:
            prefix = ""
            postfix = "## "
            output += "is %sin window until %s " % (approx, timeh.countdown(now, eta))

    if spawns >= 1:
        output += "(%s respawn since last update) " % spawns
    if target:
        postfix += ".target"
    if snippet:
        snippet = "-\n%s" % snippet

    return prefix + output + postfix + "\n" + snippet


def detail(name, tod, pop, signed_tod, signed_pop, respawn_time, plus_minus, tags, window_start, window_end, accuracy, eta, snippet):
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

    output += "{LAST TOD}      [%s] signed by %s\n" \
              "{LAST POP}      [%s] signed by %s\n" \
              "{RESPAWN TIME}  [%s±%s]\n" \
              "{TAGS}          [%s]\n" \
              % (tod, simple_username(signed_tod),
                 pop, simple_username(signed_pop),
                 respawn_time, plus_minus,
                 print_tags)
    if plus_minus:
        output += "{WINDOW OPEN}   [%s]\n" \
                  "{WINDOW CLOSE}  [%s]\n" \
                  % (window_start, window_end)

    output += "{ETA}           [%s]\n" \
              "{LAST SNIPPET}  [%s]\n" \
              % (eta, snippet)
    return output


def last_update(name, last, mode="tod"):
    output = "[" + name + "] last %s {%s}\n" % (mode, last)
    return output


def output_list(content: list):
        output = ""
        for line in content:
            output += line
        if output == "":
            output = "Empty!"
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

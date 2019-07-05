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


def time_remaining(name, eta, plus_minus, window, spawns, accuracy, target, v_target_tag=True):
    now = timeh.now()
    postfix = ""
    prefix = ""
    output = "+ [" + name + "] "
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
            output += "is %sin .window until %s " % (approx, timeh.countdown(now, eta))

    if spawns >= 1:
        output += "(%s respawn since last update) " % spawns
    if target == "auto" and v_target_tag:
        postfix += ".sticky_target"
    if target == "manual" and v_target_tag:
        postfix += ".new_target"

    return prefix + output + postfix + "\n"


def merb_status(merb, timezone,
                v_trackers=False, v_only_active_trackers=False, v_info=False, v_target_tag=True):

    body_trackers = ""
    body_info = ""
    header = time_remaining(merb.name,
                            merb.eta,
                            merb.plus_minus,
                            merb.window,
                            merb.spawns,
                            merb.accuracy,
                            merb.target,
                            v_target_tag)

    # Force hide trackers on merb not in window.
    if not merb.plus_minus or not merb.is_in_window():
        v_trackers = False

    # Force active trackers view when merb is in window and a target
    if merb.target and merb.is_in_window() and not v_info:
        v_trackers = True
        v_only_active_trackers = True

    # Force Info view when merb has no eta and disable trackers
    if not merb.has_eta():
        v_info = True
        v_trackers = False

    # GET TRACKERS (with mode 2 or higher)
    if v_trackers:
        if v_only_active_trackers:
            # Show only active trackers on reduced version
            body_trackers += tracker_list(merb, timezone, only_active=True)
        else:
            # Show all trackers on long version
            body_trackers += tracker_list(merb, timezone)

    # GET ALL INFO (with mode 3 or higher or when no ETA available
    if v_info:
        tod_tz = timeh.change_naive_to_tz(merb.tod, timezone).strftime(config.DATE_FORMAT_PRINT)
        pop_tz = timeh.change_naive_to_tz(merb.pop, timezone).strftime(config.DATE_FORMAT_PRINT)
        w_start_tz = timeh.change_naive_to_tz(merb.window["start"], timezone).strftime(config.DATE_FORMAT_PRINT)
        w_end_tz = timeh.change_naive_to_tz(merb.window["end"], timezone).strftime(config.DATE_FORMAT_PRINT)
        tags = ""
        for t in merb.tag:
            tags += "%s -" % t
        if tags:
            tags = tags[0:-2]

        body_info += "Timezone %s\n\n" % timezone
        body_info += " LAST TOD      {%s} - signed by %s\n" \
                     " LAST POP      {%s} - signed by %s\n" \
                     " RESPAWN TIME  {%s±%s}\n" \
                     " TAGS          {%s}\n" \
                     % (tod_tz, simple_username(merb.tod_signed_by),
                        pop_tz, simple_username(merb.pop_signed_by),
                        merb.respawn_time, merb.plus_minus,
                        tags)
        if merb.plus_minus:
            body_info += " WINDOW OPEN   {%s}\n" \
                         " WINDOW CLOSE  {%s}\n" \
                          % (w_start_tz, w_end_tz)

        body_info += " LAST SNIPPET  {%s}\n" % merb.snippet

    # Assemble the Output
    output = header
    if body_trackers:
        output += header_sep(header, "-") + body_trackers + "\n"
    if body_info:
        output += header_sep(header, "-") + body_info + "\n\n"

    return output


def track_msg(author, merb, track_mode, time, time_future):

    if not time_future:
        output = "%s starts tracking [%s]  %s" % (author, merb.name, track_mode)
    else:
        time_remaining = timeh.countdown(timeh.now(), time)
        output = "%s will start tracking [%s] in %s %s" % (author, merb.name, time_remaining, track_mode)
    return output


def merb_trackers_recap(merb, mode, timezone):
    output = "[" + merb.name + "] "
    if mode == "pop":
        output += "popped at {%s} %s\n" % (merb.pop.strftime(config.DATE_FORMAT_PRINT), timezone)
    if mode == "tod":
        output += "died at {%s} %s\n" % (merb.tod.strftime(config.DATE_FORMAT_PRINT), timezone)
    output += header_sep(output, "-")
    output += tracker_list(merb, timezone)
    return output


def tracker_list(merb, timezone, only_active=False):
    output = ""
    if only_active:
        trackers = merb.get_active_trackers()
    else:
        trackers = reversed(merb.trackers)

    for tracker in trackers:
        tracker_name = next(iter(tracker))

        tracker_start = timeh.change_tz(timeh.naive_to_tz( tracker[tracker_name]["time_start"], "UTC"), timezone)
        tracker_stop = False
        tracker_mode = tracker[tracker_name]["mode"]
        if "time_stop" in tracker[tracker_name]:
            tracker_stop = timeh.change_tz(timeh.naive_to_tz( tracker[tracker_name]["time_stop"], "UTC"), timezone)
            output += "  "
        else:
            output += "# "
        if tracker[tracker_name]["time_start"] > timeh.now():
            output += "%s will start tracking at {%s %s} " % (tracker_name, tracker_start.strftime(config.DATE_FORMAT_PRINT), timezone)
        else:
            output += "%s started tracking at {%s %s} " % (tracker_name, tracker_start.strftime(config.DATE_FORMAT_PRINT), timezone)
        if tracker_stop:
            output += "ended at {%s %s} " % (tracker_stop.strftime(config.DATE_FORMAT_PRINT), timezone)
            output += "(%s) " % timeh.countdown(tracker_start, tracker_stop)
        else:
            if timeh.naive_to_tz(timeh.now(), "UTC") < tracker_start:
                virtual_end = tracker_start
            else:
                virtual_end = timeh.naive_to_tz(timeh.now(), "UTC")
            output += "(%s so far) " % timeh.countdown(tracker_start, virtual_end)
        if tracker_mode:
            output += ".%s" % tracker_mode
        output += "\n"
    if not output:
        if only_active:
            output = "No active Tracker :(\n"
        else:
            output = "No Tracker :(\n"

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


def header_sep(header, sep="-"):
    return (sep * len(header.strip())) + "\n"

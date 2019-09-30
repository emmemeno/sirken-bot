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

    if my_type == "BLOCK":
        prefix = postfix = "```\n"
    elif my_type == "CSS":
        prefix = "```css\n"
        postfix = "```\n"
    elif my_type == "YELLOW":
        prefix = "```fix\n+ "
        postfix = "```\n"
    elif my_type == "RED":
        prefix = "```diff\n"
        postfix = "```\n"
    elif my_type == "MD":
        prefix = "```md\n"
        postfix = "```\n"
    elif my_type == "BLUE":
        prefix = "```asciidoc\n= "
        postfix = "```\n"
    elif my_type == "SINGLE":
        prefix = postfix = "`\n"
    else:
        prefix = postfix = ""

    return prefix + text + postfix


def time_remaining(merb, v_target_tag=True):
    now = timeh.now()
    postfix = ""
    prefix = ""
    output = "- [" + merb.name + "] "
    approx = ""
    if merb.accuracy <= 0 or merb.spawns == 1:
        approx = "{roughly} "
    if merb.accuracy <= -1 or merb.spawns > 1:
        approx = "{very roughly} "
    if not merb.plus_minus:
        if now > merb.eta:
            output += "ToD is too old. "
        else:
            output += "will %sspawn in %s " % (approx, timeh.countdown(now, merb.eta))
    else:
        if merb.is_alive():
            output += "popped %s ago " % timeh.countdown(merb.pop, timeh.now())

        elif now > merb.window['end']:
            output += "window is closed "

        elif now < merb.window['start']:
            output += "window will %sopen in %s " % (approx, timeh.countdown(now, merb.eta))

        elif merb.window['start'] <= now <= merb.window['end']:
            prefix = ""
            postfix = "## "
            output += "is %sin .window until %s " % (approx, timeh.countdown(now, merb.eta))

    if merb.spawns >= 1:
        output += "(%s respawn since last update) " % merb.spawns
    if merb.target == "auto" and v_target_tag:
        postfix += ".sticky_target"
    if merb.target == "manual" and v_target_tag:
        postfix += ".new_target"

    return prefix + output + postfix + "\n"


def merb_status(merb, timezone,
                v_trackers=False, v_only_active_trackers=False, v_info=False, v_target_tag=True, v_single=True):

    body_trackers = ""
    body_info = ""
    header = time_remaining(merb, v_target_tag)

    # Force hide trackers on merb not in window.
    if not merb.plus_minus or not merb.is_in_window() and not v_info:
        v_trackers = False

    # Force active trackers view when merb is in window and a target or active trackers are present
    if (merb.target and merb.is_in_window() and not v_info) or merb.get_trackers():
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
            active_trackers = tracker_list(merb, timezone, only_active=True)
            if active_trackers:
                body_trackers += active_trackers
            else:
                body_trackers = " No trackers!\n"

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
                     " ALIASES       {%s}\n" \
                     % (tod_tz, simple_username(merb.tod_signed_by),
                        pop_tz, simple_username(merb.pop_signed_by),
                        merb.respawn_time, merb.plus_minus,
                        tags, merb.print_aliases())
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


def merb_update_recap(merb, mode, timezone):
    output = "[" + merb.name + "] "

    if mode == "pop":
        time_pop = timeh.change_tz(timeh.naive_to_tz(merb.pop, "UTC"), timezone)
        output += "popped at {%s %s} - signed by %s\n" % (time_pop.strftime(config.DATE_FORMAT_PRINT),
                                                          timezone,
                                                          simple_username(merb.pop_signed_by))
    if mode == "tod":
        time_tod = timeh.change_tz(timeh.naive_to_tz(merb.tod, "UTC"), timezone)
        output += "died at {%s %s} - signed by %s\n" % (time_tod.strftime(config.DATE_FORMAT_PRINT),
                                                        timezone,
                                                        simple_username(merb.tod_signed_by))
    trackers = tracker_list(merb, timezone)

    if trackers:
        output += header_sep(output, "-")
        output += trackers

    return output


def tracker_list(merb, timezone, only_active=False):
    output = ""

    for tracker in merb.trackers:
        tracker_name = tracker
        try:
            tracker_name = config.authenticator.users[tracker].name

        except:
            pass
        output += "%s " % tracker_name

    if output:
        output = "Active Trackers: %s\n" % output

    return output


def get_self_track_info(user_id, trackers):
    tracker = trackers.get_tracker(user_id)
    if not tracker:
        return "You are not tracking :("

    output = 'You are tracking: '
    for merb in tracker['merbs']:
        output += "[%s] " % merb.name
    output += "since %s" % timeh.countdown(tracker['date'], timeh.now())
    return output


def last_update(name, last, mode="tod"):
    output = "[" + name + "] last %s {%s}\n" % (mode, last)
    return output


def print_stop_tracking_msg(who, what, mode, start_time):
    output_msg = ''
    if start_time > timeh.now():
        total_duration = ""
    else:
        total_duration = "(Total Time: %s)" % timeh.countdown(start_time, timeh.now())

    if who == 'You':
        output_msg += f"You stop tracking {what} "
    else:
        output_msg += f"{who} stops tracking {what} "
    if mode:
        output_msg += f"[{mode}] "
    output_msg += f"= {total_duration}"

    return output_msg


def print_dkp_tracking_msg(who, what, mode, start_time):
    if start_time > timeh.now():
        total_duration = ""
    else:
        total_duration = "(Total Time: %s)" % timeh.countdown(start_time, timeh.now())

    output_msg = f"{who} tracked {what} "
    if mode:
        output_msg += f"[{mode}] "
    output_msg += f"= {total_duration}"

    return output_msg

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

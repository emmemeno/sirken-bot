from timeit import default_timer as timer
import auth
import line_parser
import errors
import messagecomposer
import config
import re
import timehandler as timeh
import logging
import operator

logger = logging.getLogger("Input")


class SirkenCommands:

    def __init__(self, d_client, my_auth, merbs_list, my_help, watcher):
        self.d_client = d_client
        self.authenticator = my_auth
        self.merbs = merbs_list
        self.lp = line_parser.LineParser(merbs_list)
        self.helper = my_help
        self.watch = watcher
        self.input_author = None
        self.input_author_roles = None
        self.input_channel = None

    ##################
    # PROCESS THE LINE
    ##################
    def process(self, author, channel, line):

        t_start = timer()

        self.lp.process(line)

        # continue only if there is a command
        if not self.lp.cmd:
            return False

        self.input_author = author
        self.input_channel = channel

        cmd_list = {
            "about": self.cmd_about,  # About
            "help": self.cmd_help,  # Help
            "hi": self.cmd_help,
            "get": self.cmd_get,  # Get a single Merb
            "tod": self.cmd_tod,  # Update a Merb Status
            "pop": self.cmd_pop,  # Set pop time to now
            "track": self.cmd_track,  # Set pop time to now
            "watch": self.cmd_watch,  # Watch a merb
            "target": self.cmd_target,
            "earthquake": self.cmd_earthquake,  # Reset all pop times to now
            "merbs": self.cmd_merbs,  # Get Aliases
            "roles": self.cmd_roles,
            "setrole": self.cmd_set_role,
            "users": self.cmd_users,
            "echo": self.cmd_echo,
            "missing": self.cmd_missing
        }

        func = cmd_list.get(self.lp.cmd, lambda: {"destination": self.input_author,
                                                  "content": messagecomposer.prettify(errors.error_command()),
                                                  "broadcast": False})
        output = func()
        t_end = timer()
        processing_time = round(t_end - t_start, 5)
        logger.info("%s - %s (%s)" % (messagecomposer.simple_username(str(self.input_author)), line, processing_time))

        # clearing the line
        self.lp.clear()

        return output

    #########################
    # PRINT THE ABOUT MESSAGE
    #########################
    def cmd_about(self):
        return {"destination": self.input_author,
                "content": self.helper.get_about(),
                'broadcast': False}

    #######
    # HELP
    #######
    @auth.cmd("help")
    def cmd_help(self):
        return {"destination": self.input_author,
                "content": self.helper.get_help(self.lp.param),
                'broadcast': False}

    ######
    # GET
    ######
    @auth.cmd("get")
    def cmd_get(self):
        output_channel = self.input_channel
        output_broadcast = False

        # print merbs in target
        if "target" in self.lp.key_words:
            output_content = "NEXT TARGETS\n"
            output_content += "=" * (len(output_content)-1) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.get_all_targets())
        # print merbs by tag
        elif self.lp.tag:
            output_content = "#%s\n" % self.lp.tag.upper()
            output_content += "=" * len(self.lp.tag) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.get_all_by_tag(self.lp.tag))

        # print only merbs in windows
        elif "window" in self.lp.key_words:
            output_content = "MERBS IN WINDOW\n"
            output_content += "=" * len(output_content) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.get_all_window())

        # print a list of all merbs
        elif "all" in self.lp.key_words:
            output_content = messagecomposer.output_list(self.merbs.get_all(self.lp.timezone, 'countdown'))

        # print single merb
        elif self.lp.merb_found:
            if "info" in self.lp.key_words:
                output_content = self.lp.merb_found.print_long_info(self.lp.timezone)
            else:
                output_content = self.lp.merb_found.print_short_info(with_snippet=True)

        # no parameter recognized but a guessed merb
        elif self.lp.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            output_channel = self.input_author

        # no parameter recognized
        else:
            output_content = errors.error_param(self.lp.cmd, "Missing Parameter. ")
            output_channel = self.input_author

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast}

    ###############
    # MISSING
    ###############
    @auth.cmd("missing")
    def cmd_missing(self):
        output_channel = self.input_channel
        output_broadcast = False
        output_content = "MISSING ETA"

        if self.lp.tag:
            output_content += " - #%s" % self.lp.tag.upper()
        output_content += " - Timezone: %s" % self.lp.timezone

        output_content += "\n"
        output_content += "=" * len(output_content) + "\n\n"
        output_content += messagecomposer.output_list(self.merbs.get_all_missing(self.lp.timezone, self.lp.tag))

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast}

    ######################
    # UPDATE TIME OF DEATH
    ######################
    @auth.cmd("tod")
    def cmd_tod(self):
        return self.update_merb("tod")

    ######################
    # UPDATE POP TIME/DATE
    ######################
    @auth.cmd("pop")
    def cmd_pop(self):
        return self.update_merb("pop")

    def update_merb(self, mode="tod"):
        output_channel = self.input_channel
        output_broadcast = False
        output_second_message = False
        secondary_messages = list()

        # Check for approx, exact for default
        approx = 1
        approx_output = ""
        if "approx" in self.lp.key_words:
            approx = 0
            approx_output = "~"

        # If there is a Merb
        if self.lp.merb_found:

            # Assume now for pop without times
            if not self.lp.my_date and mode == "pop":
                self.lp.my_date = timeh.now()
            # Check if we have a date
            if self.lp.my_date:
                # UPDATE THE TOD
                if mode == "tod":
                    self.lp.merb_found.update_tod(self.lp.my_date, str(self.input_author), self.lp.snippet, approx)
                if mode == "pop":
                    self.lp.merb_found.update_pop(self.lp.my_date, str(self.input_author), self.lp.snippet)
                    if config.BATPHONE and self.lp.merb_found.target:
                        logger.info("%s BATPHONED in %s" % (self.lp.merb_found.name, config.BROADCAST_BP_CHANNELS))
                        secondary_messages.append({"destination": config.BROADCAST_BP_CHANNELS,
                                                 "content": "@everyone %s" % self.lp.merb_found.name,
                                                 "broadcast": False})

                # save merbs timers
                self.merbs.save_timers()

                # save targets
                self.merbs.save_targets()

                output_date = timeh.change_tz(timeh.naive_to_tz(self.lp.my_date, "UTC"),
                                              self.lp.timezone)
                output_content = "[%s] updated! New %s: {%s %s} - %ssigned by %s" % \
                                 (self.lp.merb_found.name,
                                  mode,
                                  output_date.strftime(config.DATE_FORMAT_PRINT),
                                  self.lp.timezone,
                                  approx_output,
                                  self.input_author.name)
                if self.lp.snippet:
                    output_content += "\n-\n%s" % self.lp.snippet

                output_broadcast = self.get_broadcast_channels(config.BROADCAST_TOD_CHANNELS)

                # TRACKERS

                if self.lp.merb_found.trackers:
                    trackers_recap = messagecomposer.track_recap(self.lp.merb_found, self.lp.timezone, mode)
                    self.lp.merb_found.wipe_trackers()

                    # save trackers
                    self.merbs.save_trackers()

                    secondary_messages.append({"destination": config.BROADCAST_TRACK_CHANNELS,
                                               "content": messagecomposer.prettify(trackers_recap, "CSS")[0],
                                               "broadcast": False})

            else:
                output_content = errors.error_param(self.lp.cmd, "Time Syntax Error. ")
                output_channel = self.input_author

        # If there is a guessed merb
        elif self.lp.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            output_channel = self.input_author
        # If no merb
        else:
            output_channel = self.input_author
            output_content = errors.error_merb_not_found()

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast,
                'secondary_messages': secondary_messages}

    ###############
    # TRACK A MERB
    ###############
    @auth.cmd("track")
    def cmd_track(self):
        output_channel = self.input_channel
        output_broadcast = False

        if "target" in self.lp.key_words:
            # Cycles all target merbs and print trackers
            output_content = ""
            for merb in self.merbs.merbs:
                if merb.target:
                    output_content += messagecomposer.track_recap(merb, self.lp.timezone)

        elif not self.lp.merb_found and "target" not in self.lp.key_words:
            output_channel = self.input_author
            if self.lp.merb_guessed:
                output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            else:
                output_content = "Merb not found"
        # Merb has no eta
        elif not self.lp.merb_found.has_eta():
            output_channel = self.input_author
            output_content = "Merb has not ETA. ToD too old?"
        # Merb is not a window type
        elif not self.lp.merb_found.plus_minus:
            output_channel = self.input_author
            output_content = "Merb is not a window type!"
        else:
            # if no time is passed, assumed now
            time = timeh.now()
            if self.lp.my_date:
                time = self.lp.my_date

            # if merb is not in window, time is its eta
            if not self.lp.merb_found.in_window():
                time = self.lp.merb_found.eta

            output_time = timeh.change_tz(timeh.naive_to_tz(time, "UTC"), self.lp.timezone)
            user_is_tracking = self.lp.merb_found.get_single_active_tracker(self.input_author.name)
            # FTE MODE
            if "fte" in self.lp.key_words:
                track_mode = "fte"

            else:
                track_mode = ""

            if "off" in self.lp.key_words or "stop" in self.lp.key_words or "end" in self.lp.key_words:
                # check if the user is currently tracking
                if not user_is_tracking:
                    output_channel = self.input_author
                    output_content = "You are not tracking %s" % self.lp.merb_found.name
                else:
                    my_tracker = self.lp.merb_found.stop_tracker(self.input_author.name, time)

                    # save trackers
                    self.merbs.save_trackers()

                    output_content = "%s stops tracking [%s] at {%s} %s %s" % (self.input_author.name,
                                                                               self.lp.merb_found.name,
                                                                               output_time.strftime(config.DATE_FORMAT_PRINT),
                                                                               self.lp.timezone,
                                                                               track_mode)
                    output_content += "(%s) " % timeh.countdown(my_tracker['time_start'], my_tracker['time_stop'])
                    output_broadcast = self.get_broadcast_channels(config.BROADCAST_TRACK_CHANNELS)

            elif "start" in self.lp.key_words:
                if user_is_tracking:
                    output_channel = self.input_author
                    output_content = "You are already tracking [%s]" % self.lp.merb_found.name
                else:

                    self.lp.merb_found.start_tracker(self.input_author.name, time, track_mode)

                    # save trackers
                    self.merbs.save_trackers()

                    output_content = "%s starts tracking [%s] at {%s} %s %s" % (self.input_author.name,
                                                                             self.lp.merb_found.name,
                                                                             output_time.strftime(config.DATE_FORMAT_PRINT),
                                                                             self.lp.timezone,
                                                                             track_mode)
                    output_broadcast = self.get_broadcast_channels(config.BROADCAST_TRACK_CHANNELS)
            else:
                # print track info
                output_content = messagecomposer.track_recap(self.lp.merb_found, self.lp.timezone)
            # print("ALL TRACKERS for %s:\n%s" % (self.lp.merb_found, self.lp.merb_found.trackers))
            # print("ACTIVE TRACKERS for %s:\n%s" % (self.lp.merb_found, self.lp.merb_found.get_active_trackers()))
            # output_broadcast = config.BROADCAST_TRACK_CHANNELS

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast}

    ##################
    # SET UP A WATCHER
    ##################
    @auth.cmd("watch")
    def cmd_watch(self):
        output_channel = self.input_author
        output_broadcast = False

        if self.lp.merb_found:
            # search for minutes param
            minutes = 30
            reg_min = re.search(r"\b(\d+)\b", self.lp.param)
            if reg_min:
                minutes = int(reg_min.group(0))
            off = False
            if "off" in self.lp.key_words:
                off = True
                output_content = "Track OFF for [%s]" % self.lp.merb_found.name
            else:
                output_content = "Track ON for [%s], I will alert you %d before ETA" % \
                                 (self.lp.merb_found.name, minutes)

            self.watch.switch(self.input_author.id, self.lp.merb_found.name, minutes, off)

        # If there is a guessed merb
        elif self.lp.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            output_channel = self.input_author

        # if no merb is passed but OFF parameter is, toggle off all alarms
        elif "off" in self.lp.key_words:
            self.watch.all_off(self.input_author.id)
            output_content = "All alarms are set to OFF"

        # If not params are passed get the full list of tracked merbs
        else:
            tracked_merbs = self.watch.get_all(self.input_author.id)
            if not tracked_merbs:
                output_content = "No merbs tracked :("
            else:
                output_content = ""
                for tmerb in tracked_merbs:
                    output_content += '[%s] will alert %d minutes before ETA\n' % (tmerb, tracked_merbs[tmerb])

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                "broadcast": output_broadcast}

    ##################
    # SET A TARGET
    ##################
    @auth.cmd("target")
    def cmd_target(self):
        output_channel = self.input_channel
        output_broadcast = False

        if self.lp.merb_found:
            if "off" in self.lp.key_words:
                self.lp.merb_found.target = False
                output_content = "Target OFF for [%s] " % self.lp.merb_found.name
            else:
                self.lp.merb_found.target = True
                output_content = "Target ON for [%s]" % self.lp.merb_found.name

            output_content += "- signed by %s" % self.input_author.name
            self.merbs.save_targets()
            output_broadcast = self.get_broadcast_channels(config.BROADCAST_TOD_CHANNELS)
        # If there is a guessed merb
        elif self.lp.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            output_channel = self.input_author
        else:
            output_content = errors.error_param(self.lp.cmd, "Missing Parameter. ")
            output_channel = self.input_author

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                "broadcast": output_broadcast}

    ############
    # EARTHQUAKE
    ############
    @auth.cmd("earthquake")
    def cmd_earthquake(self):
        output_channel = self.input_channel
        output_broadcast = False

        if self.lp.my_date:
            for merb in self.merbs.merbs:
                merb.update_pop(self.lp.my_date, str(self.input_author), "earthquake pop")

            self.merbs.save_timers()

            output_date = timeh.change_tz(timeh.naive_to_tz(self.lp.my_date, "UTC"), self.lp.timezone)
            output_content = "Earthquake! All pop times updated [%s] %s, signed by %s" % \
                             (output_date.strftime(config.DATE_FORMAT_PRINT),
                              self.lp.timezone,
                              self.input_author.name
                              )
            output_broadcast = self.get_broadcast_channels(config.BROADCAST_TOD_CHANNELS)

        else:
            output_content = errors.error_param(self.lp.cmd, "Time Syntax Error. ")
            output_channel = self.input_author

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast,
                'earthquake': True}

    ########################
    # PRINT ALIASES OF MERBS
    ########################
    @auth.cmd("merbs")
    def cmd_merbs(self):
        output_content = messagecomposer.output_list(self.merbs.get_all_meta())

        return {"destination": self.input_author,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': False}

    ########################
    # ROLES LIST/RELOAD
    ########################
    @auth.cmd("roles")
    def cmd_roles(self):
        output_channel = self.input_author
        output_broadcast = False
        output_content = ""

        # Reload Roles
        if "reload" in self.lp.key_words:
            self.authenticator.reload_discord_roles()
            self.authenticator.reload_discord_users()
            output_content += "{Roles Reloaded}\n\n"

        output_discord_roles_content = "DISCORD ROLES\n=============\n"
        for d_role in self.authenticator.roles.discord_roles:
            converted_role = self.authenticator.roles.convert_discord_role_into_bot_role(str(d_role.id))

            output_discord_roles_content += "- [%s server] %s (%d) -> %s\n" % \
                              (d_role.guild,
                               d_role.name,
                               d_role.id,
                               converted_role)

        output_bot_roles_content = "\nBOT ROLES\n=========\n"
        for b_role in self.authenticator.roles.bot_roles:
            output_bot_roles_content += "- %s\n" % b_role
            for resource in self.authenticator.roles.bot_roles[b_role]:
                output_bot_roles_content += "    - %s " % resource
                for permission in self.authenticator.roles.bot_roles[b_role][resource]:
                    output_bot_roles_content += "[%s] " % permission
                output_bot_roles_content += "\n"
            output_bot_roles_content += "\n"

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_discord_roles_content + output_bot_roles_content),
                'broadcast': output_broadcast}

    ##########
    # ROLE SET
    ##########
    @auth.cmd("setrole")
    def cmd_set_role(self):
        output_channel = self.input_author
        output_broadcast = False
        output_content = ""

        b_role = d_role = False
        if self.lp.param:

            # Find the discord_role_id
            reg = re.search(r"\b(\d+)\b", self.lp.param)
            if reg:
                d_role = self.authenticator.roles.check_discord_role(reg.group(0))

            # Find the Bot_Roles
            bot_roles_list = self.authenticator.roles.get_bot_roles_list()
            regex = ""
            for role in bot_roles_list:
                regex += "%s|" % role
            regex = r"\b(" + regex[:-1] + r")\b"
            reg = re.search(regex, self.lp.param)
            if reg:
                b_role = reg.group(0)

            if not isinstance(d_role, auth.DiscordRole):
                output_content = "Discord Role ID not found! Type !roles to list them"
            elif not b_role:
                output_content = "Bot Role not found! Type !roles to list them"
            else:
                self.authenticator.roles.assign_discord_role_to_bot_role(str(d_role.id), b_role)
                output_content += "Discord Role [%s] {%s} assigned to Bot Role [%s]\n\n" %\
                                  (d_role.name, d_role.id, b_role)
                output_content += "Commands for this new role:\n%s" %\
                                  self.authenticator.acl.which_permissions_any([b_role], "command")
                self.authenticator.reload_discord_roles()
                self.authenticator.reload_discord_users()

        else:
            output_content = errors.error_param(self.lp.cmd, "Missing Parameter. ")

        return {"destination": output_channel,
                "content":  messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast}

    ########################
    # USERS LIST/RELOAD
    ########################
    @auth.cmd("users")
    def cmd_users(self):
        output_channel = self.input_author
        output_broadcast = False

        if "reload" in self.lp.key_words:
            self.authenticator.reload_discord_users()
            return {"destination": output_channel,
                    "content": messagecomposer.prettify("Users Reloaded!\n", "CSS"),
                    'broadcast': output_broadcast}

        # Find the Bot_Roles
        b_role = False
        bot_roles_list = self.authenticator.roles.get_bot_roles_list()
        regex = ""
        if self.lp.param:
            for role in bot_roles_list:
                regex += "%s|" % role
            regex = r"\b(" + regex[:-1] + r")\b"
            reg = re.search(regex, self.lp.param)
            if reg:
                b_role = reg.group(0)

        if "all" not in self.lp.key_words and b_role not in bot_roles_list:
            output_content = "Bot Role not found! Type !roles to list them or !users all"
            return {"destination": output_channel,
                    "content": messagecomposer.prettify(output_content, "CSS"),
                    'broadcast': output_broadcast}

        output_content = "USERS\n=====\n"
        get_key = operator.attrgetter("name")
        for user in (sorted(self.authenticator.users.values(), key=lambda mbr: get_key(mbr).lower())):
            if "all" in self.lp.key_words or b_role in user.b_roles:
                user_name = user.name
                user_bot_roles = ""
                for user_b_role in user.b_roles:
                    user_bot_roles += ".%s " % user_b_role
                user_guilds = ""
                for guild in user.guilds:
                    user_guilds += "{%s} " % guild
                user_guilds = user_guilds[:-1]
                output_content += "- [%s] %s - %s\n" % (user_name, user_guilds, user_bot_roles)

        return {"destination": output_channel,
                "content": messagecomposer.prettify(output_content, "CSS"),
                'broadcast': output_broadcast}

    ###########
    # BROADCAST
    ###########
    @auth.cmd("echo")
    def cmd_echo(self):

        return {"destination": self.input_channel,
                "content": messagecomposer.prettify(self.lp.param, "CSS"),
                'broadcast': self.get_broadcast_channels(config.BROADCAST_TOD_CHANNELS)}

    ########################
    # LEAVE ALL SERVERS
    ########################
    @auth.cmd("guild")
    def leave_all_guilds(self):

        return {"destination": self.input_channel,
                "content": messagecomposer.prettify("Farewell!", "CSS"),
                'broadcast': self.get_broadcast_channels(config.BROADCAST_TOD_CHANNELS),
                'action': 'leave_all_guilds'}

    #########################
    # GET BROADCAST CHANNELS
    #########################
    def get_broadcast_channels(self, channels):
        broadcast_channels = list()
        for channel in channels:
            if not self.input_channel.id == channel:
                broadcast_channels.append(channel)
        return broadcast_channels

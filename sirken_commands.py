import config
import re
import line_parser
import timehandler as timeh
import auth
import messagecomposer
import errors
import logging
import operator

logger = logging.getLogger("Input Output")


class SirkenCommands:

    def __init__(self, d_client, my_auth, merbs_list, my_help, watcher, trackers):
        self.d_client = d_client
        self.authenticator = my_auth
        self.merbs = merbs_list
        self.lp = line_parser.LineParser(merbs_list)
        self.helper = my_help
        self.watch = watcher
        self.trackers = trackers
        self.input_author = None
        self.input_author_roles = None
        self.input_channel = None
        self.broadcast_channels = None

    ##################
    # PROCESS THE LINE
    ##################
    def process(self, message):

        self.input_author = message.author
        self.input_channel = message.channel

        self.lp.process(message.content)

        # continue only if there is a command
        if not self.lp.cmd:
            return False

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

        func = cmd_list.get(self.lp.cmd, lambda: False)
        output = func()

        # clearing the line
        self.lp.clear()
        return output

    #########################
    # PRINT THE ABOUT MESSAGE
    #########################
    def cmd_about(self):
        return [{'destination': self.input_author,
                 'content': self.helper.get_about(),
                 'decoration': None}]

    #######
    # HELP
    #######
    @auth.cmd("help")
    def cmd_help(self):
        return [{'destination': self.input_author,
                 'content': self.helper.get_help(self.lp.param),
                 'decoration': None}]

    ######
    # GET
    ######
    @auth.cmd("get")
    def cmd_get(self):
        output_channel = self.input_channel

        # print merbs in target
        if "target" in self.lp.key_words:
            output_content = "NEXT TARGETS\n"
            output_content += "=" * (len(output_content)-1) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.print_all_targets())
        # print merbs by tag
        elif self.lp.tag:
            output_content = "#%s\n" % self.lp.tag.upper()
            output_content += "=" * len(self.lp.tag) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.print_all_by_tag(self.lp.tag))

        # print only merbs in windows
        elif "window" in self.lp.key_words:
            output_content = "MERBS IN WINDOW\n"
            output_content += "=" * len(output_content) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.print_all_in_window())

        # print a list of all merbs
        elif "all" in self.lp.key_words:
            output_content = messagecomposer.output_list(self.merbs.print_all())

        elif "today" in self.lp.key_words:
            output_content = messagecomposer.output_list(self.merbs.print_all(limit_hours=24))

        # print single merb
        elif self.lp.merb_found:
            if "info" in self.lp.key_words:
                output_content = self.lp.merb_found.print_long_info(self.lp.timezone, v_single=True)

            else:
                output_content = self.lp.merb_found.print_short_info(self.lp.timezone,
                                                                     v_trackers=True,
                                                                     v_only_active_trackers=True,
                                                                     v_single=True)

        # no parameter recognized but a guessed merb
        elif self.lp.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            output_channel = self.input_author

        # no parameter recognized
        else:
            output_content = errors.error_param(self.lp.cmd, "Missing Parameter. ")
            output_channel = self.input_author

        return [{'destination': output_channel,
                 'content': output_content,
                 'decoration': "CSS"}]

    ###############
    # MISSING
    ###############
    @auth.cmd("missing")
    def cmd_missing(self):
        output_channel = self.input_channel
        output_content = "MISSING ETA"

        if self.lp.tag:
            output_content += " - #%s" % self.lp.tag.upper()
        output_content += " - Timezone: %s" % self.lp.timezone

        output_content += "\n"
        output_content += "=" * len(output_content) + "\n\n"
        output_content += messagecomposer.output_list(self.merbs.get_all_missing(self.lp.timezone, self.lp.tag))

        return [{'destination': output_channel,
                'content': output_content,
                'decoration': "CSS"}]

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
        output_messages = list()
        mode_word = ""

        # Check for approx, exact for default
        approx = 1
        if "approx" in self.lp.key_words:
            approx = 0

        # Assume now for !pop without time
        if not self.lp.my_date and mode == "pop":
            self.lp.my_date = timeh.now()

        if not self.lp.merb_found and self.lp.merb_guessed:
            return [{'destination': self.input_author,
                     'content': "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name,
                     'decoration': 'BLOCK'}]

        if not self.lp.merb_found and not self.lp.merb_guessed:
            return [{'destination': self.input_author,
                     'content': "Merb not found!",
                     'decoration': 'BLOCK'}]
        if not self.lp.my_date:
            return [{'destination': self.input_author,
                     'content': "Time Syntax error.\n Type {!help %s} for the correct use" % mode,
                     'decoration': 'BLOCK'}]

        # A Printable, timezone converted date
        output_tz_time = timeh.change_naive_to_tz(self.lp.my_date, self.lp.timezone).strftime(config.DATE_FORMAT_PRINT)
        # Is a target?
        is_target = self.lp.merb_found.is_target()
        # UPDATE THE TOD
        if mode == "tod":
            self.lp.merb_found.update_tod(self.lp.my_date, str(self.input_author), self.lp.snippet, approx)
            mode_word = "died"

        # UPDATE THE POP
        if mode == "pop":
            if not self.lp.merb_found.update_pop(self.lp.my_date, str(self.input_author), self.lp.snippet):
                return [{'destination': self.input_author,
                         'content': "%s has a more recent tod time. Pop is rejected" % self.lp.merb_found.name,
                         'decoration': 'BLOCK'}]

            mode_word = "popped"

            # BATPHONE IT
            if config.BATPHONE and "bp" in self.lp.key_words:

                output_messages.append({'destination': self.d_client.get_channel(config.BROADCAST_BP_CHANNEL),
                                        'content': f"{config.TAG_BATPHONE} {self.lp.merb_found.name}",
                                        'decoration': None})

                # Send a raid-add command to DKP BOT if Target
                if config.DKP_BRIDGE:
                    output_messages.append({'destination': self.d_client.get_channel(config.DKP_ADD_RAID_CHANNEL),
                                            'content': f"{config.DKP_ADD_RAID_COMMAND} "
                                                       f"{self.lp.merb_found.get_shortest_alias()} "
                                                       f"({self.lp.merb_found.name})",
                                            'decoration': False})

        # Answer message
        output_messages.append({'destination': self.input_channel,
                                'content': "[%s] %s at {%s %s}" % (self.lp.merb_found.name,
                                                                   mode_word,
                                                                   output_tz_time,
                                                                   self.lp.timezone),
                                'decoration': "CSS"})

        # Recap of merb status
        output_messages.append({'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                                'content': messagecomposer.merb_update_recap(self.lp.merb_found,
                                                                             mode,
                                                                             "UTC"),
                                'decoration': "CSS"})

        # Stop trackers tracking the merb and alert them
        stopped_trackers = self.trackers.stop_trackers_by_merb(self.lp.merb_found)
        for tracker in stopped_trackers:
            tracker_id = next(iter(tracker))

            # Check if tracking other merbs
            tracker_ended = tracker[tracker_id]['ended']
            tracker_info = tracker[tracker_id]['info']
            if not tracker_ended:
                private_content = "%s %s but you are still tracking " % (self.lp.merb_found.name, mode_word)
                for merb in tracker_info['merbs']:
                    private_content += "[%s] " % merb.name
                private_content += "\nTo stop tracking please {!track stop}"
            else:
                output_messages += self.assemble_stop_tracking_messages(tracker_id, tracker[tracker_id]['info'])

        # save merbs timers
        self.merbs.save_timers()
        # save targets
        self.merbs.save_targets()
        # Save trackers
        self.trackers.save()

        return output_messages

    ############
    # EARTHQUAKE
    ############
    @auth.cmd("earthquake")
    def cmd_earthquake(self):
        output_messages = list()
        eq_content = "%s BROADCASTS, 'Minions gather, their forms appearing" \
                     " as time and space coalesce.'" % self.input_author.name
        self.lp.snippet = "Earthquake"

        # Assume now for when no time
        if not self.lp.my_date:
            self.lp.my_date = timeh.now()

        # BATPHONE IT
        if config.BATPHONE:
            output_messages.append({'destination': self.d_client.get_channel(config.BROADCAST_BP_CHANNEL),
                                    'content': f"{config.TAG_BATPHONE} EARTHQUAKE",
                                    'decoration': None})

        output_messages.append({'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                                'content': eq_content,
                                'decoration': 'BLOCK'})
        output_messages.append({'destination': self.input_channel,
                                'content': "Earthquake!!!",
                                'decoration': 'BLOCK'})

        for merb in self.merbs.merbs:
            merb.update_pop(self.lp.my_date, str(self.input_author), self.lp.snippet)

        for tracker in self.trackers.stop_all_trackers():
            tracker_id = next(iter(tracker))

            output_messages += self.assemble_stop_tracking_messages(tracker_id, tracker[tracker_id]['info'])

        # save merbs timers
        self.merbs.save_timers()
        # save targets
        self.merbs.save_targets()
        # Save trackers
        self.trackers.save()

        return output_messages

    def assemble_stop_tracking_messages(self, tracker_id, info):
        messages = []
        tracker_name = tracker_id
        # Get tracker name
        try:
            tracker_name = config.authenticator.users[tracker_id].name
        except:
            logger.error(f"Can't retrieve {tracker_id} name")

        private_content = messagecomposer.print_stop_tracking_msg("You",
                                                                  info['what'],
                                                                  info['mode'],
                                                                  info['date']
                                                                  )
        public_content = messagecomposer.print_stop_tracking_msg(tracker_name,
                                                                 info['what'],
                                                                 info['mode'],
                                                                 info['date']
                                                                 )
        dkp_content = messagecomposer.print_dkp_tracking_msg(tracker_name,
                                                             info['what'],
                                                             info['mode'],
                                                             info['date']
                                                             )
        decoration = "YELLOW"

        messages.append({'destination': self.d_client.get_user(tracker_id),
                         'content': private_content,
                         'decoration': decoration})
        messages.append({'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                         'content': public_content,
                         'decoration': decoration})
        if config.DKP_BRIDGE:
            messages.append({'destination': self.d_client.get_channel(config.DKP_TRACKING_CHANNEL),
                             'content': dkp_content,
                             'decoration': decoration})

        return messages

    def assemble_start_tracking_messages(self, what, tracked_merbs, mode=''):
        messages = []
        output_private_content = ''
        if mode:
            mode = f"[{mode}]"

        for merb in tracked_merbs:
            if merb.is_in_window():
                output_private_content += f"You start tracking {merb.name} {mode}\n"
            else:
                time_to_start = timeh.countdown(timeh.now(), merb.window['start'])
                output_private_content += f"You will start tracking {merb.name} in {time_to_start} {mode}\n"

        output_private_content += "\nRemember to {!track stop} when leaving or {!pop merb} at spawn time.\n" \
                                  "If you want to Batphone please {!pop merb_name BP}"

        messages.append({'destination': self.input_author,
                         'content': output_private_content,
                         'decoration': 'CSS'})

        messages.append({'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                         'content': f"{self.input_author.name} starts tracking {what.capitalize()} {mode}",
                         'decoration': 'YELLOW'})

        return messages

    ###############
    # TRACK A MERB
    ###############
    @auth.cmd("track")
    def cmd_track(self):

        output_messages = list()
        author_tracker = self.trackers.get_tracker(self.input_author.id)

        # GET INFORMATION ABOUT SELF TRACKING
        if "info" in self.lp.key_words:
            return [{'destination': self.input_author,
                     'content': messagecomposer.get_self_track_info(self.input_author.id, self.trackers),
                     'decoration': 'CSS'}]

        # STOP TRACKING
        elif "off" in self.lp.key_words or "stop" in self.lp.key_words or "end" in self.lp.key_words:
            if not author_tracker:
                return [{'destination': self.input_author,
                         'content': "You are not tracking anything",
                         'decoration': 'CSS'}]

            stopped_tracker = self.trackers.stop_tracker_by_user(self.input_author.id)
            output_messages += self.assemble_stop_tracking_messages(self.input_author.id, stopped_tracker)

             # Save trackers
            self.trackers.save()
            self.merbs.save_timers()
            return output_messages

        # START SINGLE TRACKING
        elif "start" in self.lp.key_words:
            # Don'start if you are already tracking
            if author_tracker:
                return [{'destination': self.input_author,
                         'content': "You are already tracking [%s]\n"
                                    "Please {!track stop} before tracking something else" % author_tracker['what'],
                         'decoration': 'CSS'}]

            # TRACK MODE
            if "fte" in self.lp.key_words:
                track_mode = "fte"
            elif "buff" in self.lp.key_words:
                track_mode = "buff"
            else:
                track_mode = ""

            # START TRACKING A GROUP
            if self.lp.tag:
                started_tracker = self.trackers.add_tracker(self.input_author.id,
                                                            self.lp.tag,
                                                            timeh.now(),
                                                            track_mode,
                                                            self.merbs)

                if not started_tracker:
                    return [{'destination': self.input_author,
                             'content': "There are no merbs to track in %s\n"
                                        "Type {!get %s} for updated times" % (self.lp.tag, self.lp.tag),
                             'decoration': 'CSS'}]

                tracked_merbs = self.trackers.get_tracked_merb_by_user(self.input_author.id)
                output_messages += self.assemble_start_tracking_messages(self.lp.tag, tracked_merbs, track_mode)

                # Save trackers
                self.trackers.save()
                self.merbs.save_timers()
                return output_messages
            else:
                # Merb not found
                if not self.lp.merb_found:
                    if self.lp.merb_guessed:
                        output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
                    else:
                        output_content = "Merb not found"
                    return [{'destination': self.input_author,
                             'content': output_content,
                             'decoration': 'BLOCK'}]

                # Merb has no eta
                elif not self.lp.merb_found.has_eta():
                    return [{'destination': self.input_author,
                             'content': "%s has not ETA. ToD too old?" % self.lp.merb_found.name,
                             'decoration': 'BLOCK'}]

                # Merb is not a window type
                elif not self.lp.merb_found.plus_minus:
                    return [{'destination': self.input_author,
                             'content': "%s is not a window type!" % self.lp.merb_found.name,
                             'decoration': 'BLOCK'}]

                # Merb window opening is too far away
                elif timeh.next_future(12) < self.lp.merb_found.window['start']:
                    return [{'destination': self.input_author,
                             'content': "%s's window is out of range" % self.lp.merb_found.name,
                             'decoration': 'BLOCK'}]
                else:
                    started_tracker = self.trackers.add_tracker(self.input_author.id,
                                                                self.lp.merb_found,
                                                                timeh.now(),
                                                                track_mode,
                                                                self.merbs)

                    output_messages += self.assemble_start_tracking_messages(self.lp.merb_found.name, [self.lp.merb_found], track_mode)

                    # Save trackers
                    self.trackers.save()
                    self.merbs.save_timers()
                    return output_messages
        else:
            return [{'destination': self.input_author,
                     'content': "Missing parameters!\nType {!help track} for the correct use",
                     'decoration': 'CSS'}]

    ##################
    # SET UP A WATCHER
    ##################
    @auth.cmd("watch")
    def cmd_watch(self):

        # Output information about watched merbs
        if "info" in self.lp.key_words:
            output_content = ""
            for merb, time in self.watch.get_all(self.input_author.id).items():
                output_content += "[%s] - alert %s minutes before ETA\n" % (merb, time)
            if not output_content:
                output_content = "You are not watching any merb"

            return [{'destination': self.input_author,
                     'content': output_content,
                     'decoration': 'CSS'}]

        # Merb not found
        if not self.lp.merb_found:
            if self.lp.merb_guessed:
                output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            else:
                output_content = "Merb not found"
            return [{'destination': self.input_author,
                     'content': output_content,
                     'decoration': 'BLOCK'}]

        # Find Minutes
        minutes = 30
        reg_min = re.search(r"\b(\d+)\b", self.lp.param)
        if reg_min:
            minutes = int(reg_min.group(0))

        if "off" in self.lp.key_words:
            off = True
            private_content = "Watch OFF for [%s]" % self.lp.merb_found.name
        else:
            off = False
            private_content = "Watch ON for [%s], I will alert you %d before ETA" % \
                              (self.lp.merb_found.name, minutes)

        self.watch.switch(self.input_author.id, self.lp.merb_found.name, minutes, off)

        return [{'destination': self.input_author,
                 'content': private_content,
                 'decoration': 'CSS'}]

    ##################
    # SET A TARGET
    ##################
    @auth.cmd("target")
    def cmd_target(self):
        output_channel = self.input_channel
        output_messages = list()

        # Merb not found
        if not self.lp.merb_found:
            if self.lp.merb_guessed:
                output_content = "Merb not found. Did you mean %s?" % self.lp.merb_guessed.name
            else:
                output_content = "Merb not found"
            return [{'destination': self.input_author,
                     'content': output_content,
                     'decoration': 'BLOCK'}]

        if self.lp.merb_found:
            if "off" in self.lp.key_words:
                self.lp.merb_found.switch_target(False)
                output_content = "- %s is no more a target " % self.lp.merb_found.name
            else:
                if "sticky" in self.lp.key_words:
                    self.lp.merb_found.switch_target("auto")
                    output_content = "+ %s is a sticky target! " % self.lp.merb_found.name
                else:
                    self.lp.merb_found.switch_target("manual")
                    output_content = "+ %s is a new target! " % self.lp.merb_found.name

            output_content += "- signed by %s" % self.input_author.name
            self.merbs.save_targets()
        else:
            output_content = errors.error_param(self.lp.cmd, "Missing Parameter. ")
            output_channel = self.input_author

        output_messages.append({'destination': output_channel,
                                'content': output_content,
                                'decoration': 'CSS'})
        output_messages.append({'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                                'content': output_content,
                                'decoration': 'MD'})

        return output_messages

    ########################
    # PRINT ALIASES OF MERBS
    ########################
    @auth.cmd("merbs")
    def cmd_merbs(self):
        output_content = messagecomposer.output_list(self.merbs.print_all_meta())

        return [{'destination': self.input_author,
                 'content': output_content,
                 'decoration': 'CSS'}]

    ########################
    # ROLES LIST/RELOAD
    ########################
    @auth.cmd("roles")
    def cmd_roles(self):
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

        return [{'destination': self.input_author,
                 'content': output_discord_roles_content + output_bot_roles_content,
                 'decoration': 'CSS'}]

    ##########
    # ROLE SET
    ##########
    @auth.cmd("setrole")
    def cmd_set_role(self):
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

        return [{'destination': self.input_author,
                'content':  output_content,
                'decoration': "CSS"}]

    ########################
    # USERS LIST/RELOAD
    ########################
    @auth.cmd("users")
    def cmd_users(self):

        if "reload" in self.lp.key_words:
            self.authenticator.reload_discord_users()
            return [{'destination': self.input_author,
                    'content': "Users Reloaded!\n",
                    'decoration': 'CSS'}]

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
            return [{'destination': self.input_author,
                    'content': output_content,
                    'decoration': 'CSS'}]

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

        return [{'destination': self.input_author,
                'content': output_content,
                'decoration': "CSS"}]

    ###########
    # BROADCAST
    ###########
    @auth.cmd("echo")
    def cmd_echo(self):

        return [{'destination': self.d_client.get_channel(config.BROADCAST_CHANNEL),
                 'content': self.lp.param,
                 'decoration': 'CSS'}]

    ########################
    # LEAVE ALL SERVERS
    ########################
    @auth.cmd("guild")
    def leave_all_guilds(self):

        return {'destination': self.input_channel,
                'content': messagecomposer.prettify("Farewell!", "CSS"),
                'broadcast': self.broadcast_channels,
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

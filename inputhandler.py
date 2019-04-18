import discord
import line_parser
import errors
import messagecomposer
import config
import re
import timehandler as timeh


class InputHandler:

    def __init__(self, merbs_list, my_help, out_h, watcher):
        self.merbs = merbs_list
        self.lineparser = line_parser.LineParser(merbs_list)
        self.helper = my_help
        self.out_h = out_h
        self.watch = watcher
        self.input_author = None
        self.input_channel = None

    ##################
    # PROCESS THE LINE
    ##################
    def process(self, author, channel, line):

        self.lineparser.process(line)

        # continue only if there is a command
        if not self.lineparser.cmd:
            return False
        # logging.debug('Process Line: Channel {%s} [%s] %s', channel, author, line)
        self.input_author = author
        self.input_channel = channel

        cmd_list = {
            "about": self.cmd_about,  # About
            "help": self.cmd_help,  # Help
            "hi": self.cmd_help,
            "get": self.cmd_get,  # Get a single Merb
            "tod": self.cmd_tod,  # Update a Merb Status
            "pop": self.cmd_pop,  # Set pop time to now
            "watch": self.cmd_watch,  # Watch a merb
            "earthquake": self.cmd_earthquake,  # Reset all pop times to now
            "merbs": self.cmd_merbs,  # Get Aliases
        }

        func = cmd_list.get(self.lineparser.cmd, lambda: {"destination": self.input_author,
                                                          "content": errors.error_command(),
                                                          "broadcast": False})
        output = func()

        # clearing the line
        self.lineparser.clear()

        return output

    #########################
    # PRINT THE ABOUT MESSAGE
    #########################
    def cmd_about(self):
        return {"destination": self.input_author,
                "content": self.helper.get_about(),
                'broadcast': False}

    ################
    # GET THE HELPER
    ################
    def cmd_help(self):
        return {"destination": self.input_author,
                "content": self.helper.get_help(self.lineparser.param),
                'broadcast': False}

    ###################
    # PRINT SINGLE ONE
    ###################
    def cmd_get(self):
        output_channel = self.input_channel
        output_broadcast = False

        # print a list of all merbs
        if self.lineparser.all:
            output_content = messagecomposer.output_list(self.merbs.get_all(self.lineparser.timezone, 'countdown'))

        # print merbs by tag
        elif self.lineparser.tag:
            output_content = "#%s\n" % self.lineparser.tag.upper()
            output_content += "=" * len(self.lineparser.tag) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.get_all_by_tag(self.lineparser.tag))

        # print only merbs in windows
        elif self.lineparser.window:
            output_content = "MERBS IN WINDOW\n"
            output_content += "=" * len(output_content) + "\n\n"
            output_content += messagecomposer.output_list(self.merbs.get_all_window())

        # print single merb
        elif self.lineparser.merb:
            if self.lineparser.info:
                output_content = self.lineparser.merb.print_long_info(self.lineparser.timezone)
            else:
                output_content = self.lineparser.merb.print_short_info()

        # no parameter recognized but a guessed merb
        elif self.lineparser.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lineparser.merb_guessed.name
            output_channel = self.input_author

        # no parameter recognized
        else:
            output_content = errors.error_param(self.lineparser.cmd, "Missing Parameter. ")
            output_channel = self.input_author

        return {"destination": output_channel,
                "content": output_content,
                'broadcast': output_broadcast}

    ######################
    # UPDATE TIME OF DEATH
    ######################
    def cmd_tod(self):
        return self.update_merb("tod")

    ######################
    # UPDATE POP TIME/DATE
    ######################
    def cmd_pop(self):
        return self.update_merb("pop")

    def update_merb(self, mode="tod"):
        output_channel = self.input_channel
        output_broadcast = False

        # Check for approx, exact for default
        approx = 1
        approx_output = ""
        if self.lineparser.approx:
            approx = 0
            approx_output = "~"

        # If there is a Merb
        if self.lineparser.merb:
            # Check if we have a date
            if self.lineparser.my_date:
                # UPDATE THE TOD
                if mode == "tod":
                    self.lineparser.merb.update_tod(self.lineparser.my_date, str(self.input_author), approx)
                if mode == "pop":
                    self.lineparser.merb.update_pop(self.lineparser.my_date, str(self.input_author))
                # save merbs
                self.merbs.save_timers()
                output_date = timeh.change_tz(timeh.naive_to_tz(self.lineparser.my_date, "UTC"),
                                              self.lineparser.timezone)
                output_content = "[%s] updated! New %s: {%s %s} - %ssigned by %s" % \
                                 (self.lineparser.merb.name,
                                  mode,
                                  output_date.strftime(config.DATE_FORMAT_PRINT),
                                  self.lineparser.timezone,
                                  approx_output,
                                  messagecomposer.simple_username(str(self.input_author)))
                # BROADCAST if message is a private one
                if isinstance(self.input_channel, discord.abc.PrivateChannel):
                    output_broadcast = config.BROADCAST_TOD_CHANNELS

            else:
                output_content = errors.error_param(self.lineparser.cmd, "Time Syntax Error. ")
                output_channel = self.input_author

        # If there is a guessed merb
        elif self.lineparser.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lineparser.merb_guessed.name
            output_channel = self.input_author
        # If no merb
        else:
            output_channel = self.input_author
            output_content = errors.error_merb_not_found()

        return {"destination": output_channel,
                "content": output_content,
                'broadcast': output_broadcast}

    ##################
    # SET UP A WATCHER
    ##################
    def cmd_watch(self):
        output_channel = self.input_author
        output_broadcast = False

        if self.lineparser.merb:
            # search for minutes param
            minutes = 30
            reg_min = re.search(r"\b(\d+)\b", self.lineparser.param)
            if reg_min:
                minutes = int(reg_min.group(0))

            if self.lineparser.off:
                output_content = "Track OFF for [%s]" % self.lineparser.merb.name
            else:
                output_content = "Track ON for [%s], I will alert you %d before ETA" % \
                                 (self.lineparser.merb.name, minutes)

            self.watch.switch(self.input_author.id, self.lineparser.merb.name, minutes, self.lineparser.off)

        # If there is a guessed merb
        elif self.lineparser.merb_guessed:
            output_content = "Merb not found. Did you mean %s?" % self.lineparser.merb_guessed.name
            output_channel = self.input_author

        # if no merb is passed but OFF parameter is, toggle off all alarms
        elif self.lineparser.off:
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
                "content": output_content,
                "broadcast": output_broadcast}

    ############
    # EARTHQUAKE
    ############
    def cmd_earthquake(self):
        output_channel = self.input_channel
        output_broadcast = False

        if self.lineparser.my_date:
            for merb in self.merbs.merbs:
                merb.update_pop(self.lineparser.my_date, str(self.input_author))

            self.merbs.save_timers()

            output_date = timeh.change_tz(timeh.naive_to_tz(self.lineparser.my_date, "UTC"), self.lineparser.timezone)
            output_content = "Earthquake! All pop times updated [%s] %s, signed by %s" % \
                             (output_date.strftime(config.DATE_FORMAT_PRINT),
                              self.lineparser.timezone,
                              self.input_author
                              )
            # BROADCAST if message is a private one
            if isinstance(self.input_channel, discord.abc.PrivateChannel):
                output_broadcast = config.BROADCAST_TOD_CHANNELS

        else:
            output_content = errors.error_param(self.lineparser.cmd, "Time Syntax Error. ")
            output_channel = self.input_author

        return {"destination": output_channel,
                "content": output_content,
                'broadcast': output_broadcast}

    ########################
    # PRINT ALIASES OF MERBS
    ########################
    def cmd_merbs(self):
        output_content = messagecomposer.output_list(self.merbs.get_all_meta())

        return {"destination": self.input_author,
                "content": output_content,
                'broadcast': False}

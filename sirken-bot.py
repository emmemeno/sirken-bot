import config
import logging
import logging.config
import re
import asyncio
import discord
from discord.ext import commands
import timehandler as timeh
import messagecomposer
import outputhandler
import npc
import watch
import helper
import errors


class InputHandler:

    def __init__(self):
        self.text = None
        self.author = None
        self.channel = None
        self.cmd = None
        self.param = None
        self.info = None
        self.timezone = "CET"

    ##################
    # PROCESS THE LINE
    ##################
    def process(self, author, channel, line):
        # deal only with lines that start with !
        if line[0] != "!":
            return False
        logging.debug('Process Line: Channel {%s} [%s] %s', channel, author, line)
        self.text = line[1:].lower()
        self.author = author
        self.channel = channel
        split_text = self.text.split(" ", 1)
        self.cmd = split_text[0]
        try:
            self.param = split_text[1]
        except IndexError:
            self.param = None

        # check if timezone is provided
        self.timezone = self.tz()

        cmd_list = {
            "about": self.about,  # About
            "help": self.help,  # Help
            "list": self.get_list,  # Get the List of Merbs
            "get": self.get_single,  # Get a single Merb
            "tod": self.update_tod,  # Update a Merb Status
            "merbs": self.alias,  # Get Aliases
            "tags": self.tags,  # Get Tags
            "windows": self.get_window,  # Get Merbs in window
            "watch": self.set_watch,  # Watch a merb
            "pop": self.update_pop,  # Set pop time to now
            "earthquake": self.earthquake,  # Reset all pop times to now
            "hi": self.help
        }
        func = cmd_list.get(self.cmd, lambda: {"destination": self.author,
                                               "content": errors.error_command(),
                                               'broadcast': False})
        return func()

    #########################
    # PRINT THE ABOUT MESSAGE
    #########################
    def about(self):
        return {"destination": self.author,
                "content": helper.get_about(),
                'broadcast': False}

    ################
    # GET THE HELPER
    ################
    def help(self):
        return {"destination": self.author,
                "content": helper.get_help(self.param),
                'broadcast': False}

    ##################
    # SET UP A WATCHER
    ##################
    def set_watch(self):
        # If not params are passed get the full list of tracked merbs
        if not self.param:
            tracked_merbs = watch.get_all(self.author.id)
            output_msg = ""
            if not tracked_merbs:
                output_msg = "No merbs tracked :("
            else:
                for tmerb in tracked_merbs:
                    output_msg += '[%s] will alert %d minutes before ETA\n' % (tmerb, tracked_merbs[tmerb])

            return {"destination": self.author,
                    "content": output_msg,
                    'broadcast': False}

        # search the merb in the param
        merb = merbs.get_single(self.param)
        # search for ON/OFF param
        mode = "ON"
        if re.search(r"\b(off)\b", self.param):
            mode = "OFF"

        if merb:
            # search for minutes param
            minutes = 30
            reg_min = re.search(r"\b(\d+)\b", self.param)
            if reg_min:
                minutes = int(reg_min.group(0))

            if mode == "ON":
                output_msg = "Track ON for [%s], I will alert you %d before ETA" % (merb.name, minutes)
            else:
                output_msg = "Track OFF for [%s]" % merb.name

            watch.switch(self.author.id, merb.name, minutes, mode)

            return {"destination": self.author,
                    "content":  output_msg,
                    'broadcast': False}
        # if no merb param is passed but OFF, toggle off all alarms
        elif mode == "OFF":
            watch.off(self.author.id)
            return {"destination": self.author,
                    "content": "All alarms are set to OFF",
                    'broadcast': False}

    ############
    # EARTHQUAKE
    ############
    def earthquake(self):
        for merb in merbs.merbs:
            merb.update_pop(timeh.now(), str(self.author))

        merbs.save_timers()
        broadcast = False
        if self.channel.is_private:
            broadcast = config.BROADCAST_TOD_CHANNELS
        return {"destination": self.channel,
                "content": "%s BROADCAST: Minions gather, their forms appearing as time and space coalesce."
                           % self.author,
                "broadcast": broadcast,
                "earthquake": self.author}

    #######################
    # PRINT MERBS IN WINDOW
    #######################
    def get_window(self):
        print_list = out_h.output_list(merbs.get_all_window())
        return {"destination": self.channel,
                "content": print_list,
                'broadcast': False}

    #################################
    # PRINT LIST OF MERBS (COUNTDOWN)
    #################################
    def get_list(self):
        input_tag = None
        # search for a tag
        if self.param:
            tags = merbs.get_re_tags().lower()
            input_tag = re.search(tags, self.param.lower())

        if input_tag:
            print_list = "%s\n" % input_tag.group(0)
            print_list += "=" * len(input_tag.group(0)) + "\n\n"
            print_list += out_h.output_list(merbs.get_all_by_tag(input_tag.group(0)))
        else:
            print_list = out_h.output_list(merbs.get_all(self.timezone, 'countdown'))

        if len(print_list) > config.MAX_BROADCAST_LENGTH:
            destination = self.author
        else:
            destination = self.channel

        return {"destination": destination,
                "content": print_list,
                'broadcast': False}

    ###################
    # PRINT SINGLE ONE
    ###################
    def get_single(self):
        if not self.param:
            return {"destination": self.author,
                    "content": errors.error_param(self.cmd, "Missing Parameter. "),
                    'broadcast': False}

        # search the merb
        merb = merbs.get_single(self.param)
        if merb:

            # search the parameter info for detailed information
            self.info = re.search(r"\b(info)\b", self.param)
            if self.info:
                content = merb.print_long_info(self.timezone)
            # countdown info
            else:
                content = merb.print_short_info()

            return {"destination": self.channel,
                    "content": content,
                    'broadcast': False}
        else:
            return {"destination": self.author,
                    "content": errors.error_merb_not_found(),
                    'broadcast': False}

    ######################
    # UPDATE POP TIME/DATE
    ######################
    def update_pop(self):
        # search the merb in the param
        merb = merbs.get_single(self.param)
        if merb:
            merb.update_pop(timeh.now(), str(self.author))
            merbs.save_timers()
            broadcast = False
            if self.channel.is_private:
                broadcast = config.BROADCAST_TOD_CHANNELS
            return {"destination": self.channel,
                    "content": "[%s] POP! (%s)" % (merb.name, self.author),
                    'broadcast': broadcast,
                    'merb_alert': merb}
        else:
            return {"destination": self.author,
                    "content": errors.error_merb_not_found(),
                    'broadcast': False
                    }

    ######################
    # UPDATE TIME OF DEATH
    ######################
    def update_tod(self):
        if not self.param:
            return {"destination": self.author,
                    "content": errors.error_param(self.cmd, "Missing Parameter. "),
                    'broadcast': False}

        merb = merbs.get_single(self.param)

        # Check if Merb exists
        if not merb:
            return {"destination": self.author,
                    "content": errors.error_merb_not_found(),
                    'broadcast': False}

        # Parse the Time. Search for "now" keyword, otherwise process line to find a valid time
        new_tod = timeh.assemble_date(self.param, self.timezone)

        # Check if time is correct
        if not new_tod:
            return {"destination": self.author,
                    "content": errors.error_param(self.cmd, "Time Syntax Error. "),
                    'broadcast': False}

        # Check for approx tag, exact for default
        approx = 1
        approx_output = ""
        if re.search(r"\b(approx)\b", self.param):
            approx = 0
            approx_output = "~"

        merb.update_tod(new_tod, str(self.author), approx)
        # save merbs
        merbs.save_timers()

        output_date = timeh.change_tz(timeh.naive_to_tz(new_tod,"UTC"), self.timezone)
        output_message = "[%s] updated! New Tod: [%s] %s, %ssigned by %s" %\
                         (merb.name, output_date.strftime(config.DATE_FORMAT_PRINT),
                          self.timezone,
                          approx_output,
                          self.author)

        # Reveal tod message if updated privately
        broadcast = False
        if self.channel.is_private:
            broadcast = config.BROADCAST_TOD_CHANNELS
        return {"destination": self.channel,
                "content": output_message,
                'broadcast': broadcast}

    ########################
    # PRINT ALIASES OF MERBS
    ########################
    def alias(self):
        content = out_h.output_list(merbs.get_all_alias())
        return {"destination": self.author,
                "content": content,
                'broadcast': False}

    ########################
    # PRINT ALL TAGS
    ########################
    def tags(self):
        content = out_h.output_list(merbs.get_all_tags())
        return {"destination": self.author,
                "content": content,
                'broadcast': False}

    ##############################
    # PARSE THE TIMEZONE PARAMETER
    ##############################
    def tz(self):
        timezone = "CET"
        if self.param:
            reg = re.search(r"\b(pst|pdt|cst|cdt|est|edt|cet|gmt)\b", self.param)
            if reg:
                timezone = reg.group(1).upper()
                if timezone == "PST" or timezone == "PDT":
                    timezone = "US/Pacific"
                if timezone == "CST"or timezone == "CDT":
                    timezone = "US/Central"
                if timezone == "EST"or timezone == "EDT":
                    timezone = "US/Eastern"
        return timezone


################################################
# BACKGROUND DIGEST FUNCTION: Tic every minute #
################################################
async def digest():
    tic = 60
    while True:
        await asyncio.sleep(tic)
        now = timeh.now()
        for merb in merbs.merbs:
            # update merb eta
            merb.eta = merb.get_eta()
            minutes_diff = (merb.eta - now).total_seconds() // 60.0

            for user in watch.users:
                destination = discord.utils.get(client.get_all_members(), id=user)
                if watch.check(user, merb.name, minutes_diff) and not merb.in_window():
                    await client.send_message(destination, messagecomposer.prettify(merb.print_short_info(), "CSS"))
                    logging.debug("ALARM TO %s: %s | ETA: %s | DIFF MINUTES: %s" %
                                  (user, merb.name, merb.eta, minutes_diff))


################################################
# BACKGROUND DAILY DIGEST: Tic every hour      #
################################################
async def daily_digest():
    # tic every hour
    tic = 60*60
    while True:
        # ...
        output = ""
        now = timeh.now()
        # tic only one time per day
        if int(now.hour) == config.DAILY_HOUR:
            print_list = merbs.get_all("CET", "countdown", limit_hours=24)
            if print_list:
                counter = len(print_list)
                print_list = out_h.output_list(print_list)
                pre_message = "Good morning nerds! %d merbs are expected today, %s.\n\n" %\
                              (counter, timeh.now().strftime("%d %b %Y"))
                post_message = "\n{Type !hi to start to interact with me}\n"
                raw_output = out_h.process(pre_message + print_list + post_message)
                for message in raw_output:
                    await send_spam(messagecomposer.prettify(message, "CSS"), config.BROADCAST_DAILY_DIGEST_CHANNELS)

        await asyncio.sleep(tic)


########
# MAIN #
########
if __name__ == "__main__":

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
    })
    logging.basicConfig(filename=config.LOG_FILE,
                        level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    # Initialize Merbs List
    merbs = npc.MerbList(config.FILE_ENTITIES, config.FILE_TIMERS, config.DATE_FORMAT, config.DATE_FORMAT_PRINT)
    merbs.order()
    # Load Helper
    helper = helper.Helper(config.HELP_FILE)
    # Load Watcher
    watch = watch.Watch(config.FILE_WATCH)
    # Initialize Output Handler
    out_h = outputhandler.OutputHandler(config.MAX_MESSAGE_LENGTH)
    # Initialize Input Handler
    in_h = InputHandler()
    # Bot Stuff
    client = commands.Bot(command_prefix="!")  # Initialise client bot

    @client.event
    async def on_ready():
        print("Sirken Bot is online and connected to Discord")
        logging.info("Sirken Bot Connected to Discord")
        # Create Background Loops
        client.loop.create_task(digest())
        client.loop.create_task(daily_digest())

    @client.event
    async def on_message(message):
        # Skip self messages
        if message.author == client.user:
            return
        # Process messages
        raw_output = in_h.process(message.author, message.channel, message.content)

        if raw_output:
            # split the output if too long
            output_message = out_h.process(raw_output["content"])
            for message in output_message:
                await client.send_message(raw_output["destination"], messagecomposer.prettify(message, "CSS"))
                if raw_output['broadcast']:
                    await send_spam(messagecomposer.prettify(message, "CSS"), raw_output['broadcast'])

            # send PM Alerts
            if 'merb_alert' in raw_output:
                await send_pop_alerts(raw_output['merb_alert'], raw_output["content"])
            # send EQ Alerts
            if 'earthquake' in raw_output:
                await send_eq_alert(raw_output['earthquake'])

    # Send Spam to Broadcast Channel
    @client.event
    async def send_spam(message, channels):
        for channel in channels:
            destination = client.get_channel(channel)
            await client.send_message(destination, message)

    # Send Earthquake Messages
    @client.event
    async def send_eq_alert(author):
        for user in watch.users:
            destination = discord.utils.get(client.get_all_members(), id=user)
            await client.send_message(destination,
                                      messagecomposer.prettify("%s BROADCAST: Minions gather, their forms appearing"
                                                               " as time and space coalesce." % author, "CSS"))
            logging.info("EARTHQUAKE!")

    # Send Pop Message
    @client.event
    async def send_pop_alerts(merb: npc.Merb, message):
        for user in watch.users:
            destination = discord.utils.get(client.get_all_members(), id=user)
            if merb.name in watch.users[user]:
                await client.send_message(destination, messagecomposer.prettify(message, "CSS"))
                logging.info("SEND ALERT. %s pop TO: %s" % (merb.name, user))


    # Run the Bot
    client.run(config.DISCORD_TOKEN)

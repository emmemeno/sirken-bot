import logging
import logging.config
import json
import re
import datetime
import pytz
import asyncio
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import config
import watch

"""" Initialize """
BROADCAST_CHANNEL = config.BROADCAST_CHANNEL
DISCORD_TOKEN = config.DISCORD_TOKEN
DATE_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT_PRINT = "%b %d %H:%M"

# Time stuff (boring!)
class Time_Handler:
    def __init__(self):
        pass

    def find_date(self, line):
        date = re.search(r"(([12]\d{3})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))", line)
        if date:
            return {"year": int(date.group(2)), "month": int(date.group(3)), "day": int(date.group(4))}

    def find_time(self, line):
        time = re.search("(([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]))", line)
        if time:
            return {"hour": int(time.group(2)), "minute": int(time.group(3))}

    def now(self):
        date_new = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        return self.naive_to_tz(date_new, 'UTC', 'UTC')

    def from_mins_ago(self,mins):
        date_new = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        return self.naive_to_tz(date_new - datetime.timedelta(minutes=int(mins)), 'UTC', 'UTC')

    def assemble_date(self, s, timezone='CET'):
        # TODO: Now and xx mins ago
        if re.search(r"\b(now)\b", s):
            return self.now()

        regex_str = r"\b(\d+) ?(mins?|minutes?) ago"
        mins_ago = re.search(regex_str, s)
        if mins_ago:
            return self.from_mins_ago(mins_ago.group(1))

        time_in = self.find_time(s)
        date_in = self.find_date(s)
        # time is mandatory
        if not time_in:
            return False

        # try to validate the date
        try:
            date_new = datetime.datetime(year=date_in['year'],
                                         month=date_in['month'],
                                         day=date_in['day'],
                                         hour=time_in['hour'],
                                         minute=time_in['minute'])
        except:
            logging.debug("Date format error.")
            # if date is not provided, use actual date and replace hour and minute
            date_new = datetime.datetime.utcnow().replace(hour=time_in['hour'],
                                                          minute=time_in['minute'],
                                                          second=0,
                                                          microsecond=0)
        return self.naive_to_tz(date_new,timezone, 'UTC')

    def naive_to_tz(self, mydate, tz_from="CET", tz_to="CET"):
        local = pytz.timezone(tz_from)
        current_date = local.localize(mydate)
        tz_convert_to = pytz.timezone(tz_to)
        return current_date.astimezone(tz_convert_to)

    def change_tz(self, mydate, target_timezone="CET"):
        tz_convert_to = pytz.timezone(target_timezone)
        return mydate.astimezone(tz_convert_to)


# Class to fancy compose and format the output message
class Message_Composer:

    def prettify(self, text, type="BLOCK", pre_content=""):

        if type == "BLOCK":
            prefix = "```\n"
            postfix = prefix

        elif type == "CSS":
            prefix = "```css\n"
            postfix = "```\n"

        elif type == "SINGLE":
            prefix = "`\n"
            postfix = prefix

        elif type == None:
            prefix = ""
            postfix = prefix

        return pre_content + prefix + text + postfix

    def countdown(self, d_to, d_from):
        output = ""
        date_diff = d_from - d_to
        seconds_diff = date_diff.total_seconds()
        days = int(seconds_diff // (60 * 60 * 24))
        hours = int((seconds_diff - days*86400) // (60 * 60))
        minutes = int((seconds_diff // 60) % 60)
        if days == 1:
            output += "1 day "
        if days > 1:
            output += str(days) + " days "
        if hours == 1:
            output += "1 hour "
        if hours > 1:
            output += str(hours) + " hours "
        if hours and minutes:
            output += "and "
        if minutes == 1:
            output += "1 minute"
        if minutes > 1 or minutes == 0:
            output += str(minutes) + " minutes"

        return output

    def time_remaining(self, name, eta, plus_minus, window, spawns, accuracy, tod, author):
        now = time_h.change_tz(datetime.datetime.now(), "UTC")
        eta = time_h.change_tz(eta, "UTC")
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
            output += "will %s spawn in %s" % (approx, self.countdown(now, eta))
        if now < window['start'] and plus_minus:
            output += "window will %s open in %s" % (approx, self.countdown(now , eta))
        if window['start'] <= now <= window['end']:
            prefix = "# "
            postfix = "<-"
            output += "in window until %s " % self.countdown(now , eta)
        # output += " - {ToD: %s} signed by %s" % (tod.strftime(DATE_FORMAT_PRINT), author)
        return prefix + output + postfix + "\n"

    def detail(self,name, tod, pop, signed, respawn_time, plus_minus, window_start, window_end, accuracy, eta):
        output = "%s\n" % (name)

        for c in name:
            output += "="

        output += "\n"

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

    def alias(self, name, alias):
        output = "[%s] " % name
        for alt in alias:
            output += "{%s} " % alt
        output += "\n"
        return output

class Json_Handler:

    def __init__(self,url):
        self.url_merb = url
        self.merbs = self.load_merbs()

    def load_merbs(self):
        with open(self.url_merb) as f:
            return json.load(f)

    def save_merbs(self,merb_list):
        with open(self.url_merb, 'w') as outfile:
            json.dump(merb_list.serialize(), outfile, indent=2)
        logging.info("Json Saved")

# Class that define Merb info and a bunch of utilities
class Merb:
    def __init__(self, name, alias, respawn_time, plus_minus, tod, pop, signed, accuracy, recurring):

        utc = pytz.utc
        # Complete name of the Merb
        self.name = name
        # Aliases

        self.alias = alias
        # Respawn Time

        self.respawn_time = respawn_time
        # Viariance

        self.plus_minus = plus_minus
        # Time of Death
        self.tod = utc.localize(datetime.datetime.strptime(tod, DATE_FORMAT))

        # Pop Time
        self.pop = utc.localize(datetime.datetime.strptime(pop, DATE_FORMAT))

        # Author of the last ToD
        self.signed = signed

        # Accuracy. 0 for approx time, 1 for exact time, -1 when pop > tod
        self.accuracy = accuracy

        # If the spawn is recurring. (ex scout)
        self.recurring = recurring

        # Number of spawns since last tod (for recurring mobs)
        self.spawns = 0

        # Spawn Windows {"start"} {"end"}
        if self.tod > self.pop:
            self.window = self.get_window(self.tod)
        else:
            self.window = self.get_window(self.pop)
            self.accuracy = -2

        # Eta for the spawn/window start/window end
        self.eta = self.get_eta()

    def __str__(self):
        return 'Name {} - Respawn Time {}±{} - ToD {}' \
               ' - Window Starts {} - Window ends {}' \
               ' - ETA: {}' \
                .format(self.name,
                        self.respawn_time,
                        self.plus_minus,
                        self.tod,
                        self.window["start"],
                        self.window["end"],
                        self.eta
                        )

    def get_window(self, from_date):
        w_start = from_date + datetime.timedelta(hours=self.respawn_time) - datetime.timedelta(hours=self.plus_minus)
        w_end = from_date + datetime.timedelta(hours=self.respawn_time) + datetime.timedelta(hours=self.plus_minus)
        return {"start": w_start, "end": w_end}

    def update_tod(self, new_tod, author, approx=1):
        self.tod = new_tod
        self.signed = author
        self.accuracy = approx
        self.window = self.get_window(new_tod)
        self.eta = self.get_eta()
        logging.info("%s TOD updated by %s! New Tod: %s, accuracy: %s" % (self.name, self.signed, self.tod, self.accuracy))

    def update_pop(self, new_pop, author):
        self.pop = time_h.now()
        self.signed = author
        self.window = self.get_window(new_pop)
        self.eta = self.get_eta()
        logging.info("%s POP updated by %s! New pop: %s" % (self.name, self.signed, self.pop))

    def get_eta(self, virtual_tod=None):

        eta = time_h.naive_to_tz(datetime.datetime(1981, 2, 13, 00, 00), "UTC", "UTC")

        # virtual tod is last saved tod if this function is directly called
        if not virtual_tod:
            virtual_tod = self.tod
            self.spawns = 0

        # virtual tod is last saved pop if the latter is newer than the former
        if self.pop > virtual_tod:
            self.accuracy = -1
            virtual_tod = self.pop

        # get now date to calculate the timeframe
        now = time_h.naive_to_tz(datetime.datetime.now(), tz_to="UTC")
        delta_hour = datetime.timedelta(hours=self.respawn_time)

        # merb has no window and spawn in the future
        if self.plus_minus == 0 and now < (virtual_tod + delta_hour):
            eta = virtual_tod + delta_hour

        # merb has window and we are before window opens
        if now < self.window["start"] and self.plus_minus:
            eta = self.window["start"]

        # we are in window
        if self.window["start"] < now < self.window["end"]:
            eta = self.window["end"]

        # if the merb is a recurring one and we are past the calculated eta...
        # set a new tod for recurring mob (scout)
        if self.recurring and self.plus_minus == 0 and now >= virtual_tod + delta_hour and self.spawns < 12:
            self.spawns += 1
            eta = self.get_eta(virtual_tod + delta_hour)
            return eta

        return eta

    def in_window(self):
        now = time_h.change_tz(datetime.datetime.now(), "UTC")
        if (self.window['start'] < now < self.window['end']) and self.plus_minus:
            return True
        else:
            return False


    def ordered_eta(self):
        if self.in_window():
            return self.eta - datetime.timedelta(hours=self.plus_minus*2)
        else:
            return self.eta


    def print_short_info(self):
        self.eta = self.get_eta()
        return Message_Composer().time_remaining(self.name,self.eta, self.plus_minus, self.window, self.spawns, self.accuracy, self.tod, self.signed)

    def print_long_info(self, timezone):
        self.eta = self.get_eta()
        tod_tz = time_h.change_tz(self.tod, timezone)
        pop_tz = time_h.change_tz(self.pop, timezone)
        w_start_tz = time_h.change_tz(self.window["start"], timezone)
        w_end_tz = time_h.change_tz(self.window["end"], timezone)
        eta = time_h.change_tz(self.eta, timezone)

        return Message_Composer().detail(self.name,
                                         tod_tz.strftime(DATE_FORMAT_PRINT),
                                         pop_tz.strftime(DATE_FORMAT_PRINT),
                                         self.signed,
                                         self.respawn_time, self.plus_minus,
                                         w_start_tz.strftime(DATE_FORMAT_PRINT),
                                         w_end_tz.strftime(DATE_FORMAT_PRINT),
                                         self.accuracy,
                                         eta.strftime(DATE_FORMAT_PRINT))

    def print_alias(self):

        return Message_Composer().alias(self.name, self.alias)

    # serialize data
    def serialize(self):

        return ({self.name :
                     {'alias': self.alias,
                      "respawn_time": self.respawn_time,
                      "plus_minus": self.plus_minus,
                      "tod": self.tod.strftime(DATE_FORMAT),
                      "pop": self.pop.strftime(DATE_FORMAT),
                      "signed": self.signed,
                      "accuracy": self.accuracy,
                      "recurring": self.recurring
                      }
                 })

    # Check name in aliases
    def check_name(self, search):
        # create the reg exp with name and aliases
        keys = self.name.lower()
        for i in self.alias:
            keys += "|" + i.lower()
        reg_expr = r"\b(%s)\b" % keys
        f = re.search(reg_expr, search.lower())
        if f:
            return True
        return False

class Merb_List:

    def __init__(self, json_obj):
        self.merbs = list()
        for i in json_obj:
            if not json_obj[i].get("pop", 0):
                # Date of Last recorded earthquake
                json_obj[i]["pop"] = "2019-3-4 03:44"

            self.merbs.append(Merb(i,
                                    json_obj[i]["alias"],
                                    json_obj[i]["respawn_time"],
                                    json_obj[i]["plus_minus"],
                                    json_obj[i]["tod"],
                                    json_obj[i]["pop"],
                                    json_obj[i]["signed"],
                                    json_obj[i]["accuracy"],
                                    json_obj[i]["recurring"],
                                    )
                             )

    def order(self, order='name'):
        if order == 'name':
            self.merbs.sort(key=lambda merb: merb.name.lower())
        if order == 'eta':
            self.merbs.sort(key=lambda merb: merb.ordered_eta())


    def get_single(self,name):
        for merb in self.merbs:
            if merb.check_name(name):
                return merb
        return False

    def get_all_window(self):
        self.order('eta')
        output = ""

        for merb in self.merbs:
            if merb.window['start'] <= time_h.now() <= merb.window['end']:
                output += merb.print_short_info()
        if output == "":
            output = "Empty! :("
        return output

    def get_all(self, timezone, mode="countdown"):
        self.order('eta')
        output = ""

        for merb in self.merbs:
            if time_h.now() < merb.eta:
                # Show online merb eta in the future
                if mode == "countdown":
                    output += merb.print_short_info()
                else:
                    output += merb.print_long_info(timezone) + "\n"
        if output == "":
            output = "Empty! :("
        return output

    def get_all_alias(self):
        self.order('name')
        output = ""
        for merb in self.merbs:
            output += merb.print_alias()
        return output


    def serialize(self):
        json_output = {}
        for merb in self.merbs:
            json_output.update(merb.serialize())
        return json_output


class Helper:

    def __init__(self, json_url):
        with open(json_url) as f:
            self.help = json.load(f)

    def get_about(self):
        # if no parameter (what) is passed, return general help
        try:
            text = '\n'.join(self.help["about"])
            return Message_Composer().prettify(text, None)
        except:
            logging.error("Error getting About text")
            return False


    def get_help(self, what):
        # find the command
        commands = ""
        for c in self.help:
            commands += "|" + c
        regex = r"\b(%s)\b" % commands[1:]
        cmd = re.search(regex, what)
        # if no parameter (what) is passed, return general help
        try:
            text = '\n'.join(self.help[cmd.group(1)])
        except:
            text = '\n'.join(self.help["help"])

        return text

class OutputHandler:
    def __init__(self, max_chars):
        self.max = max_chars
        self.splitted_text = []

    def cut(self, text: str):
        # se la lunghezza del testo da processare è minore del limite, aggiungi il testo alla lista ed esci dalla funzione
        if len(text) < self.max:
            self.splitted_text.append(text)
            return self.splitted_text

        limit = text[0:self.max].rfind('\n')
        if limit == -1:
            limit = text[0:self.max].rfind(' ')
        self.splitted_text.append(text[0:limit+1])
        self.splitted_text.append(text[limit+1:])
        new_chunk = self.splitted_text[-1]
        # print('---\nNew Chunk:\n %s----\n' % new_chunk)
        if len(new_chunk) > self.max:
            self.splitted_text.pop()
            self.cut(new_chunk)

        return self.splitted_text

    def process(self,text):
        output = self.cut(text).copy()
        self.splitted_text.clear()
        return output

class Input_Handler:

    def __init__(self, out_h, merbs, time_h, json_data, helper, track):
        self.out_h = out_h
        self.time_h = time_h
        self.merbs = merbs
        self.text = ""
        self.author = ""
        self.channel = ""
        self.cmd = ""
        self.param = ""
        self.info = ""
        self.json_data = json_data
        self.helper = helper
        self.track = track
        self.timezone = "CET"


    def about(self):
        return {"destination": self.author,
                "content": helper.get_about(),
                'broadcast': False}

    def help(self):
        return {"destination": self.author,
                "content": helper.get_help(self.param),
                'broadcast': False}

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
                   "content":output_msg,
                   'broadcast': False}

        # search the merb in the param
        merb = self.merbs.get_single(self.param)
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

            watch.switch(self.author.id, merb.name, minutes,mode)

            return {"destination": self.author,
                    "content":  output_msg,
                    'broadcast': False}
        # if no merb param is passed but OFF, toggle off all alarms
        elif mode == "OFF":
            watch.off(self.author.id)
            return {"destination": self.author,
                    "content": "All alarms are set to OFF",
                    'broadcast': False}
    def earthquake(self):
        for merb in self.merbs.merbs:
            merb.update_pop(time_h.now(), str(self.author))

        self.save()
        broadcast = False
        if self.channel.is_private:
            broadcast = True
        return {"destination": self.channel,
                    "content": "%s BROADCAST: Minions gather, their forms appearing as time and space coalesce."
                                % self.author,
                    'broadcast': broadcast,
                    'earthquake': self.author}

    def get_window(self):
        print_list = self.merbs.get_all_window()
        return {"destination": self.channel,
                "content": print_list,
                'broadcast': False}

    def get_list(self):
        timezone_msg=""
        print_list = self.merbs.get_all(self.timezone, 'countdown')
        return {"destination": self.author,
                "content": print_list,
                'broadcast': False}

    def get_single(self):
        if self.param == "":
            return {"destination": self.author,
                    "content": self.error_param(self.cmd, "Missing Parameter. "),
                    'broadcast': False}
        #search the merb
        merb = self.merbs.get_single(self.param)
        if merb:
            if self.info:
                content = merb.print_long_info(self.timezone)
                content = "Timezone: %s\n\n%s" % (self.timezone, content)

            else:
                content = merb.print_short_info()

            return {"destination": self.channel,
                    "content": content,
                    'broadcast': False}
        else:
            return {"destination": self.author,
                    "content": self.error_merb_not_found(),
                    'broadcast': False}

    def update_pop(self):
        # search the merb in the param
        merb = self.merbs.get_single(self.param)
        if merb:
            merb.update_pop(time_h.now(), str(self.author))
            self.save()
            broadcast = False
            if self.channel.is_private:
                broadcast = True
            return {"destination": self.channel,
                    "content": "[%s] POP! (%s)" % (merb.name, self.author),
                    'broadcast': broadcast,
                    'merb_alert': merb}
        else:
            return {"destination": self.author,
                    "content": self.error_merb_not_found(),
                    'broadcast': False
                    }

    def update_tod(self):
        if self.param == "":
            return {"destination": self.author,
                    "content": self.error_param(self.cmd, "Missing Parameter. "),
                    'broadcast': False}

        merb = self.merbs.get_single(self.param)

        # Check if Merb exists
        if not merb:
            return {"destination": self.author,
                    "content": self.error_merb_not_found(),
                    'broadcast': False}

        # Parse the Time. Search for "now" keyword, otherwise process line to find a valid time
        new_tod = self.time_h.assemble_date(self.param, self.timezone)

        # Check if time is correct
        if new_tod == False:
            return {"destination": self.author,
                    "content": self.error_param(self.cmd, "Time Syntax Error. "),
                    'broadcast': False}

        # Check for approx tag, exact for default
        approx = 1
        approx_output = ""
        if re.search(r"\b(approx)\b", self.param):
            approx = 0
            approx_output = "~"

        merb.update_tod(new_tod, str(self.author), approx)
        #save to json
        self.save()

        output_date = time_h.change_tz(new_tod, self.timezone)
        output_message = "[%s] updated! New Tod: [%s] %s, %ssigned by %s" %\
                         (merb.name, output_date.strftime(DATE_FORMAT_PRINT), self.timezone, approx_output, self.author)
        # The Update Tod is sent into broadcast channel

        broadcast = False
        if self.channel.is_private:
            broadcast=True
        return {"destination": self.channel,
                "content": output_message,
                'broadcast': broadcast}

    def alias(self):
        content = self.merbs.get_all_alias()
        return {"destination": self.author,
                "content": content,
                'broadcast': False}

    def save(self):
        self.json_data.save_merbs(self.merbs)

    def tz(self):
        timezone = "CET"
        reg = re.search(r"\b(pst|est|cet|gmt)\b", self.param)
        if reg:
            timezone = reg.group(1).upper()
            if timezone == "PST":
                timezone = 'US/Pacific'

        return timezone

    def process(self, author, channel, line):

        #deal only with lines that start with !
        if line[0] != "!":
            return False
        logging.debug('Process Line: Channel {%s} [%s] %s', channel, author, line)
        self.text = line[1:].lower()
        self.author = author
        self.channel = channel


        splitted_text = self.text.split(" ", 1)
        self.cmd = splitted_text[0]
        try:
            self.param = splitted_text[1]
        except:
            self.param = ""

        # check if timezone is provided
        self.timezone = self.tz()
        # search the parameter info (used in !get and !list commands)
        self.info = re.search(r"\b(info)\b", self.param)

        cmd_list = {
            "about": self.about,             # About
            "help": self.help,               # Help
            "list": self.get_list,           # Get the List of Merbs
            "get": self.get_single,          # Get a single Merb
            "tod": self.update_tod,              # Update a Merb Status
            "merbs": self.alias,             # Reload from File
            "windows":  self.get_window,     # Get Merbs in window
            "watch": self.set_watch,         # Watch a merb
            "pop": self.update_pop,                 # Set pop time to now
            "earthquake": self.earthquake,   # Reset all pop times to now
            "hi": self.help
        }
        func = cmd_list.get(self.cmd, lambda: {"destination": self.author,
                                               "content": self.error_command(),
                                               'broadcast': False})
        return func()

    def error_command(self):
        return "Command not found! Type !help for help!"

    def error_param(self, cmd, error):
        return error + "For the correct syntax type [!help " + str(cmd) + "]"

    def error_time(self):
        return "Time syntax error. Type {!help tod]"

    def error_merb_not_found(self):
        return "Merb not found. For a list of named mobs type [!merbs]"

async def digest(in_h):
    tic = 60
    alert = 30
    alert_msg = ""
    while True:
        await asyncio.sleep(tic)
        now = time_h.change_tz(datetime.datetime.now(), "UTC")
        for merb in merbs.merbs:
            # update merb eta
            merb.eta = merb.get_eta()
            minutes_diff = (merb.eta - now).total_seconds() // 60.0

            for user in watch.users:
                destination = discord.utils.get(client.get_all_members(), id=user)
                if watch.check(user, merb.name, minutes_diff) and not merb.in_window():
                    await client.send_message(destination, Message_Composer().prettify(merb.print_short_info(), "CSS"))
                    logging.debug("ALARM TO %s: %s | ETA: %s | DIFF MINUTES: %s" %
                                  (user, merb.name, merb.eta, minutes_diff))


if __name__ == "__main__":

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
    })

    logging.basicConfig(filename='sirken-bot.log', level=logging.DEBUG)
    json_data = Json_Handler(config.MERBS_FILE)   # Load Json data...
    time_h = Time_Handler()                # Handler for Time Validation
    merbs = Merb_List(json_data.merbs)          # ...Initialize Merbs List
    merbs.order()
    helper = Helper(config.HELP_FILE)
    watch = watch.Watch("watch.json")
    out_h = OutputHandler(1900)
    in_h = Input_Handler(out_h, merbs, time_h, json_data, helper, watch)

    Client = discord.Client()  # Initialise Client
    client = commands.Bot(command_prefix="?")  # Initialise client bot

    @client.event
    async def on_ready():
        print("Sirken Bot is online and connected to Discord")
        logging.info("Sirken Bot Connected to Discord")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        raw_output = in_h.process(message.author, message.channel, message.content)

        if raw_output:
            # split the output if too long
            output_message = out_h.process(raw_output["content"])
            for message in output_message:
                await client.send_message(raw_output["destination"], Message_Composer().prettify(message,"CSS"))
                if raw_output['broadcast']:
                    await send_spamm(Message_Composer().prettify(message,"CSS"))

            # send PM Alerts
            if 'merb_alert' in raw_output:
                await send_pop_alerts(raw_output['merb_alert'], raw_output["content"])
            if 'earthquake' in raw_output:
                await send_eq_alert(raw_output['earthquake'])


    @client.event
    async def send_spamm(message):
        channel_to = client.get_channel(BROADCAST_CHANNEL)
        await client.send_message(channel_to, message)

    @client.event
    async def send_eq_alert(author):
        for user in watch.users:
            destination = discord.utils.get(client.get_all_members(), id=user)
            await client.send_message(destination,
                                      Message_Composer().prettify("%s BROADCAST: Minions gather, their forms appearing"
                                                                  " as time and space coalesce." % author, "CSS"))
            logging.info("EARTHQUAKE!")

    @client.event
    async def send_pop_alerts(merb: Merb, message):
        for user in watch.users:
            destination = discord.utils.get(client.get_all_members(), id=user)
            if merb.name in watch.users[user]:
                await client.send_message(destination,Message_Composer().prettify(message,"CSS"))
                logging.info("SEND ALERT. %s pop TO: %s" % (merb.name, user))
                print("SEND ALERT. %s pop TO: %s" % (merb.name, user))

    client.loop.create_task(digest(in_h))
    client.run(DISCORD_TOKEN)  # Run the Bot


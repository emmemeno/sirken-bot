import json
import datetime
import pytz
import re
import timehandler as timeh
import messagecomposer


# Class that define Merb info and a bunch of utilities
class Merb:
    def __init__(self, name, alias, respawn_time, plus_minus, tod, pop,
                 signed, accuracy, recurring, date_rec, date_print):

        self.d_rec = date_rec
        self.d_print = date_print
        utc = pytz.utc
        # Complete name of the Merb
        self.name = name

        # Aliases
        self.alias = alias

        # Respawn Time
        self.respawn_time = respawn_time

        # Variance
        self.plus_minus = plus_minus

        # Time of Death
        self.tod = utc.localize(datetime.datetime.strptime(tod, self.d_rec))

        # Pop Time
        self.pop = utc.localize(datetime.datetime.strptime(pop, self.d_rec))

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

    def update_pop(self, new_pop, author):
        self.pop = timeh.now()
        self.signed = author
        self.window = self.get_window(new_pop)
        self.eta = self.get_eta()

    def get_eta(self, virtual_tod=None):

        eta = timeh.naive_to_tz(datetime.datetime(1981, 2, 13, 00, 00), "UTC", "UTC")

        # virtual tod is last saved tod if this function is directly called
        if not virtual_tod:
            virtual_tod = self.tod
            self.spawns = 0

        # virtual tod is last saved pop if the latter is newer than the former
        if self.pop > virtual_tod:
            self.accuracy = -1
            virtual_tod = self.pop

        # get now date to calculate the timeframe
        now = timeh.naive_to_tz(datetime.datetime.now(), tz_to="UTC")
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
        now = timeh.change_tz(datetime.datetime.now(), "UTC")
        if (self.window['start'] < now < self.window['end']) and self.plus_minus:
            return True
        else:
            return False

    def print_short_info(self):
        self.eta = self.get_eta()
        return messagecomposer.time_remaining(self.name, self.eta, self.plus_minus, self.window,
                                              self.spawns, self.accuracy)

    def print_long_info(self, timezone):
        self.eta = self.get_eta()
        tod_tz = timeh.change_tz(self.tod, timezone)
        pop_tz = timeh.change_tz(self.pop, timezone)
        w_start_tz = timeh.change_tz(self.window["start"], timezone)
        w_end_tz = timeh.change_tz(self.window["end"], timezone)
        eta = timeh.change_tz(self.eta, timezone)
        return messagecomposer.detail(self.name,
                                      tod_tz.strftime(self.d_print),
                                      pop_tz.strftime(self.d_print),
                                      self.signed,
                                      self.respawn_time,
                                      self.plus_minus,
                                      w_start_tz.strftime(self.d_print),
                                      w_end_tz.strftime(self.d_print),
                                      self.accuracy,
                                      eta.strftime(self.d_print)
                                      )

    def print_alias(self):
        return messagecomposer.alias(self.name, self.alias)

    # serialize data
    def serialize(self):
        return ({self.name: {
                     'alias': self.alias,
                     "respawn_time": self.respawn_time,
                     "plus_minus": self.plus_minus,
                     "tod": self.tod.strftime(self.d_rec),
                     "pop": self.pop.strftime(self.d_rec),
                     "signed": self.signed,
                     "accuracy": self.accuracy,
                     "recurring": self.recurring}
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


# Class container of Merbs, load from JSON
class MerbList:

    def __init__(self, url_merb, date_format_rec, date_format_print):
        self.json_file = url_merb
        with open(url_merb) as f:
            json_obj = json.load(f)
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
                                   date_format_rec,
                                   date_format_print
                                   ))

    def save(self,):
        with open(self.json_file, 'w') as outfile:
            json.dump(self.serialize(), outfile, indent=2)

    def order(self, order='name'):
        if order == 'name':
            self.merbs.sort(key=lambda merb: merb.name.lower())
        if order == 'eta':
            self.merbs.sort(key=lambda merb: merb.eta)
            self.merbs.sort(key=lambda merb: merb.in_window(), reverse=True)

    def get_single(self, name):
        for merb in self.merbs:
            if merb.check_name(name):
                return merb
        return False

    def get_all_window(self):
        self.order('eta')
        output = ""

        for merb in self.merbs:
            if merb.window['start'] <= timeh.now() <= merb.window['end']:
                output += merb.print_short_info()
        if output == "":
            output = "Empty! :("
        return output

    def get_all(self, timezone, mode="countdown"):
        self.order('eta')
        output = ""

        for merb in self.merbs:
            if timeh.now() < merb.eta:
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

import config
import json
import datetime
import pytz
import re
import timehandler as timeh
import messagecomposer


# Class that define Merb info and a bunch of utilities
class Merb:
    def __init__(self, name, alias, respawn_time, plus_minus, recurring, tag, tod, pop,
                 author_tod, author_pop, accuracy, date_rec, date_print):

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

        # If the spawn is recurring. (ex scout)
        self.recurring = recurring

        # Tag of the merb
        self.tag = tag

        # Time of Death
        self.tod = datetime.datetime.strptime(tod, self.d_rec)

        # Pop Time
        self.pop = datetime.datetime.strptime(pop, self.d_rec)

        # Author of the last ToD
        self.signed_tod = author_tod

        # Author of the last pop
        self.signed_pop = author_pop

        # Accuracy. 0 for approx time, 1 for exact time, -1 when pop > tod
        self.accuracy = accuracy



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
        self.signed_tod = author
        self.accuracy = approx
        self.window = self.get_window(new_tod)
        self.eta = self.get_eta()

    def update_pop(self, new_pop, author):
        self.pop = new_pop
        self.signed_pop = author
        self.window = self.get_window(new_pop)
        self.eta = self.get_eta()

    def get_eta(self, virtual_tod=None):
        eta = datetime.datetime(1981, 2, 13, 00, 00)

        # virtual tod is last saved tod if this function is directly called
        if not virtual_tod:
            virtual_tod = self.tod
            self.spawns = 0

        # virtual tod is last saved pop if the latter is newer than the former
        if self.pop > virtual_tod:
            self.accuracy = -1
            virtual_tod = self.pop

        # get now date to calculate the timeframe
        now = datetime.datetime.utcnow()
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
        now = timeh.now()
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

        tod_tz = timeh.change_naive_to_tz(self.tod, timezone)
        pop_tz = timeh.change_naive_to_tz(self.pop, timezone)
        w_start_tz = timeh.change_naive_to_tz(self.window["start"], timezone)
        w_end_tz = timeh.change_naive_to_tz(self.window["end"], timezone)
        eta = timeh.change_naive_to_tz(self.eta, timezone)
        tz_offset = eta.strftime('%z')
        tz_offset = "{%s:%s}" % (tz_offset[0:3],tz_offset[3:])
        tz_print = "Timezone %s %s\n\n" % (timezone, tz_offset)

        return tz_print + messagecomposer.detail(self.name,
                                                 tod_tz.strftime(self.d_print),
                                                 pop_tz.strftime(self.d_print),
                                                 self.signed_tod,
                                                 self.signed_pop,
                                                 self.respawn_time,
                                                 self.plus_minus,
                                                 self.tag,
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
                             "tod": self.tod.strftime(self.d_rec),
                             "pop": self.pop.strftime(self.d_rec),
                             "signed_tod": self.signed_tod,
                             "signed_pop": self.signed_pop,
                             "accuracy": self.accuracy
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

    # Check tag
    def check_tag(self, tag):
        for i in self.tag:
            if i.lower() == tag.lower():
                return True
        return False


# Class container of Merbs, load from JSON
class MerbList:

    def __init__(self, url_entities, url_timers, date_format_rec, date_format_print):
        self.url_entities = url_entities
        self.url_timers = url_timers
        self.max_respawn_time = 0

        with open(url_entities) as f:
            json_entities = json.load(f)
        with open(url_timers) as f:
            json_timers = json.load(f)

        self.merbs = list()
        self.tags = list()
        for i in json_entities:
            limit_respawn_time = json_entities[i]["respawn_time"] + json_entities[i]["plus_minus"]
            if limit_respawn_time > self.max_respawn_time:
                self.max_respawn_time = limit_respawn_time
            if i in json_timers:
                tod = json_timers[i]["tod"]
                pop = json_timers[i]["pop"]
                signed_tod = json_timers[i]["signed_tod"]
                if "signed_pop" not in json_timers[i]:
                    signed_pop = signed_tod
                else:
                    signed_pop = json_timers[i]["signed_tod"]

                accuracy = json_timers[i]["accuracy"]
            else:
                tod = config.DATE_DEFAULT
                pop= config.DATE_DEFAULT
                signed_tod = "Default"
                signed_pop = "Default"
                accuracy = 0
            self.merbs.append(Merb(i,
                                   json_entities[i]["alias"],
                                   json_entities[i]["respawn_time"],
                                   json_entities[i]["plus_minus"],
                                   json_entities[i]["recurring"],
                                   json_entities[i]["tag"],
                                   tod,
                                   pop,
                                   signed_tod,
                                   signed_pop,
                                   accuracy,
                                   date_format_rec,
                                   date_format_print
                                   ))
            # Create a list of tag
            for tag in json_entities[i]["tag"]:
                if not tag.lower() in self.tags and tag:
                    self.tags.append(tag.lower())
            self.tags.sort()

    def save_timers(self, ):
        with open(self.url_timers, 'w') as outfile:
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
        output = list()

        for merb in self.merbs:
            if merb.window['start'] <= timeh.now() <= merb.window['end']:
                output.append(merb.print_short_info())

        return output

    def get_all(self, timezone, mode="countdown", limit_hours=None):
        if not limit_hours:
            limit_hours = self.max_respawn_time
        now = timeh.now()
        self.order('eta')
        output = list()

        for merb in self.merbs:
            date_limit = now + datetime.timedelta(hours=limit_hours)
            date_diff = date_limit - merb.eta
            hour_diff = date_diff.total_seconds() / 3600
            # print("%s HOUR DIFF %d" % (merb.name, hour_diff))
            if timeh.now() < merb.eta and hour_diff >= 0:
                # Show online merb eta in the future
                if mode == "countdown":
                    output.append(merb.print_short_info())
                else:
                    output.append(merb.print_long_info(timezone))
        return output

    def get_all_by_tag(self, tag):
        self.order('eta')
        output = list()
        for merb in self.merbs:
            if merb.check_tag(tag) and timeh.now() < merb.eta:
                output.append(merb.print_short_info())
        return output

    def get_all_alias(self):
        self.order('name')
        output = list()
        for merb in self.merbs:
            output.append(merb.print_alias())
        return output

    def get_all_tags(self):
        output = list()
        for tag in self.tags:
            output.append("%s\n" % tag)
        return output

    def get_re_tags(self):
        output = ""
        for tag in self.tags:
            output += "%s|" % tag
        output = output[:-1]
        return output

    def serialize(self):
        json_output = {}
        for merb in self.merbs:
            json_output.update(merb.serialize())
        return json_output

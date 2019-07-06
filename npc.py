import config
import json
import datetime
import timehandler as timeh
import messagecomposer


# Class that define Merb info and a bunch of utilities
class Merb:
    def __init__(self, name, alias, respawn_time, plus_minus, recurring, tag, tod, pop,
                 author_tod, author_pop, accuracy, target, trackers, snippet, date_rec, date_print):

        self.d_rec = date_rec
        self.d_print = date_print
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
        # False, "auto" or "manual"
        self.target = target
        # Time of Death
        self.tod = datetime.datetime.strptime(tod, self.d_rec)
        # Pop Time
        self.pop = datetime.datetime.strptime(pop, self.d_rec)
        # Author of the last ToD
        self.tod_signed_by = author_tod
        # Author of the last pop
        self.pop_signed_by = author_pop
        # Snippet of the last ToD
        self.snippet = snippet
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
        # Eta
        self.eta = self.get_eta()
        # Trackers
        self.trackers = trackers

    def get_window(self, from_date):
        w_start = from_date + datetime.timedelta(hours=self.respawn_time) - datetime.timedelta(hours=self.plus_minus)
        w_end = from_date + datetime.timedelta(hours=self.respawn_time) + datetime.timedelta(hours=self.plus_minus)
        return {"start": w_start, "end": w_end}

    def update_tod(self, new_tod, author, snippet="", approx=1):
        self.tod = new_tod
        self.tod_signed_by = author
        self.accuracy = approx
        self.snippet = snippet
        self.window = self.get_window(new_tod)
        self.eta = self.get_eta()
        self.auto_switch_off_target()
        self.stop_all_tracker(new_tod)

    def update_pop(self, new_pop, author, snippet=""):
        self.pop = new_pop
        self.pop_signed_by = author
        # Updates only if pop is more recent than tod
        if self.pop > self.tod:
            self.snippet = snippet
            self.window = self.get_window(new_pop)
            self.eta = self.get_eta()
            self.stop_all_tracker(new_pop)

    def get_eta(self, virtual_tod=None):
        eta = datetime.datetime.strptime(config.DATE_DEFAULT,config.DATE_FORMAT)

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
        # set a new tod for recurring mob
        if self.recurring and self.plus_minus == 0 and now >= virtual_tod + delta_hour and self.spawns < 12:
            self.spawns += 1
            eta = self.get_eta(virtual_tod + delta_hour)

        return eta

    def get_single_active_tracker(self, target):
        for my_tracker in self.trackers:
            if target in my_tracker:
                if "time_stop" not in my_tracker[target]:
                    return my_tracker[target]
        return False

    def get_active_trackers(self):
        active_trackers = list()
        for my_tracker in self.trackers:
            tracker = my_tracker[next(iter(my_tracker))]
            if "time_stop" not in tracker:
                active_trackers.append(my_tracker)
        return active_trackers

    def start_tracker(self, tracker_name, time_start, mode):
        if self.get_single_active_tracker(tracker_name):
            return False
        else:
            new_tracker = {tracker_name: {"time_start": time_start, "mode": mode}}
            self.trackers.append(new_tracker)
            return new_tracker

    def stop_tracker(self, tracker_name, time_stop):
        my_tracker = self.get_single_active_tracker(tracker_name)
        if my_tracker:
            # prevent start time newer than stop time (when booking, etc.)
            if my_tracker['time_start'] > time_stop:
                time_stop = my_tracker['time_start']
            # Stop the tracker
            my_tracker['time_stop'] = time_stop

            # Remove the tracker if he/she is a future
            if timeh.now() <= my_tracker['time_start']:
                self.trackers.remove({tracker_name: my_tracker})

            return my_tracker
        else:
            return False

    def stop_all_tracker(self, time_stop):
        for my_tracker in self.trackers:
            tracker = my_tracker[next(iter(my_tracker))]
            if "time_stop" not in tracker:
                if time_stop < tracker['time_start']:
                    time_stop = tracker['time_start']
                tracker['time_stop'] = time_stop
        return

    def wipe_trackers(self):
        del self.trackers[:]
        return

    def is_target(self):
        if self.target:
            return True
        else:
            return False

    def switch_target(self, mode):
        self.target = mode

    def auto_switch_off_target(self):
        if self.target == "manual":
            self.target = False

    def is_in_window(self):
        now = timeh.now()
        if (self.window['start'] < now < self.window['end']) and self.plus_minus:
            return True
        else:
            return False

    def has_eta(self):
        if timeh.now() < self.eta:
            return True
        else:
            return False

    def print_short_info(self, timezone="UTC", v_trackers=False, v_only_active_trackers=False, v_info=False, v_target_tag=True):
        self.eta = self.get_eta()
        return messagecomposer.merb_status(self, timezone,
                                           v_trackers=v_trackers,
                                           v_only_active_trackers=v_only_active_trackers,
                                           v_info=v_info,
                                           v_target_tag=v_target_tag)

    def print_long_info(self, timezone, v_trackers=True, v_only_active_trackers=False, v_info=True, v_target_tag=True):
        self.eta = self.get_eta()
        return messagecomposer.merb_status(self, timezone,
                                           v_trackers=v_trackers,
                                           v_only_active_trackers=v_only_active_trackers,
                                           v_info=v_info,
                                           v_target_tag=v_target_tag)

    def print_last_update(self, timezone):
        if self.pop > self.tod:
            last_update = self.pop
            mode = "pop"
        else:
            last_update = self.tod
            mode = "tod"
        last_update_tz = timeh.change_naive_to_tz(last_update, timezone)
        return messagecomposer.last_update(self.name, last_update_tz.strftime(self.d_print), mode)

    def print_meta(self):
        return messagecomposer.meta(self.name, self.alias, self.tag)

    # serialize data
    def serialize(self):
        return ({self.name: {
                             "tod": self.tod.strftime(self.d_rec),
                             "pop": self.pop.strftime(self.d_rec),
                             "signed_tod": self.tod_signed_by,
                             "signed_pop": self.pop_signed_by,
                             "accuracy": self.accuracy,
                             "snippet": self.snippet
                            }
                 })

    # Check tag
    def check_tag(self, tag):
        for i in self.tag:
            if i.lower() == tag.lower():
                return True
        return False


# Class container of Merbs, load from JSON
class MerbList:

    def __init__(self, url_entities, url_timers, url_targets, url_tracks, date_format_rec, date_format_print):
        self.url_entities = url_entities
        self.url_timers = url_timers
        self.url_targets = url_targets
        self.url_tracks = url_tracks
        self.max_respawn_time = 0

        with open(url_entities) as f:
            json_entities = json.load(f)
        with open(url_timers) as f:
            json_timers = json.load(f)
        with open(url_targets) as f:
            json_targets = json.load(f)
        with open(url_tracks) as f:
            json_tracks = json.load(f)

        self.merbs = list()
        self.tags = list()
        for i in json_entities:
            # CALCULATE LIMIT HOURS FOR GET ALL REQUESTS
            limit_respawn_time = json_entities[i]["respawn_time"] + json_entities[i]["plus_minus"]
            if limit_respawn_time > self.max_respawn_time:
                self.max_respawn_time = limit_respawn_time
            snippet = ""
            if i in json_timers:
                tod = json_timers[i]["tod"]
                pop = json_timers[i]["pop"]
                signed_tod = json_timers[i]["signed_tod"]
                if "signed_pop" not in json_timers[i]:
                    signed_pop = signed_tod
                else:
                    signed_pop = json_timers[i]["signed_pop"]

                snippet = ""
                if "snippet" in json_timers[i]:
                    snippet = json_timers[i]["snippet"]

                accuracy = json_timers[i]["accuracy"]
            else:
                tod = config.DATE_DEFAULT
                pop = config.DATE_DEFAULT
                signed_tod = "Default"
                signed_pop = "Default"
                accuracy = 0

            # LOAD TARGETS
            if i in json_targets:
                target = json_targets[i]
            else:
                target = False

            # LOAD TRACKS
            trackers = list()
            if i in json_tracks:
                for tracker in json_tracks[i]:
                    tracker_name = next(iter(tracker))
                    tracker_mode = tracker[tracker_name]["mode"]
                    time_start = datetime.datetime.strptime(tracker[tracker_name]["time_start"], config.DATE_FORMAT)
                    if tracker[tracker_name]["time_stop"]:
                        time_stop = datetime.datetime.strptime(tracker[tracker_name]["time_stop"], config.DATE_FORMAT)
                        trackers.append({tracker_name: {"time_start": time_start,
                                                        "time_stop": time_stop,
                                                        "mode": tracker[tracker_name]["mode"]}})
                    else:
                        trackers.append({tracker_name: {"time_start": time_start,
                                                        "mode": tracker[tracker_name]["mode"]}})

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
                                   target,
                                   trackers,
                                   snippet,
                                   date_format_rec,
                                   date_format_print
                                   ))
            # Create a list of tag
            for tag in json_entities[i]["tag"]:
                if not tag.lower() in self.tags and tag:
                    self.tags.append(tag.lower())
            self.tags.sort()

    def save_timers(self):
        with open(self.url_timers, 'w') as outfile:
            json.dump(self.serialize(), outfile, indent=4)

    def save_targets(self):
        with open(self.url_targets, 'w') as outfile:
            self.order('eta')
            output = {}
            for merb in self.merbs:
                if merb.target:
                    output[merb.name] = merb.target
            json.dump(output, outfile, indent=4)

    def save_trackers(self):
        with open(self.url_tracks, 'w') as outfile:
            self.order('name')
            output = {}
            for merb in self.merbs:
                if merb.trackers:
                    trackers_list = list()
                    for tracker in merb.trackers:
                        tracker_name = next(iter(tracker))
                        time_start = datetime.datetime.strftime(tracker[tracker_name]["time_start"], config.DATE_FORMAT)
                        if "time_stop" in tracker[tracker_name]:
                            time_stop = datetime.datetime.strftime(tracker[tracker_name]["time_stop"], config.DATE_FORMAT)
                        else:
                            time_stop = ""
                        trackers_list.append({tracker_name: {
                            "time_start": time_start,
                            "time_stop": time_stop,
                            "mode": tracker[tracker_name]["mode"]}
                        })

                    output.update({merb.name: trackers_list})

            json.dump(output, outfile, indent=4)

    def order(self, order='name'):
        if order == 'name':
            self.merbs.sort(key=lambda merb: merb.name.lower())
        if order == 'eta':
            self.merbs.sort(key=lambda merb: merb.eta)
            self.merbs.sort(key=lambda merb: merb.is_in_window(), reverse=True)
        if order == 'window_end':
            self.merbs.sort(key=lambda merb: merb.window['end'], reverse=True)

    def get_all_by_tag(self, tag):
        self.order('eta')
        output = list()
        for merb in self.merbs:
            if merb.check_tag(tag) and timeh.now() < merb.eta:
                output.append(merb)
        return output

    def print_all_in_window(self):
        self.order('eta')
        output = list()

        for merb in self.merbs:
            if merb.window['start'] <= timeh.now() <= merb.window['end']:
                output.append(merb.print_short_info())

        return output

    def print_all(self, timezone, mode="countdown", limit_hours=None):
        if not limit_hours:
            limit_hours = self.max_respawn_time
        now = timeh.now()
        self.order('eta')
        output = list()

        for merb in self.merbs:
            date_limit = now + datetime.timedelta(hours=limit_hours)
            date_diff = date_limit - merb.eta
            hour_diff = date_diff.total_seconds() / 3600
            if timeh.now() < merb.eta and hour_diff >= 0:
                # Show online merb eta in the future
                if mode == "countdown":
                    output.append(merb.print_short_info())
                else:
                    output.append(merb.print_long_info(timezone))
        return output

    def print_all_by_tag(self, tag):
        self.order('eta')
        output = list()
        for merb in self.merbs:
            if merb.check_tag(tag) and timeh.now() < merb.eta:
                output.append(merb.print_short_info())
        return output

    def print_all_targets(self):
        self.order('eta')
        output = list()
        for merb in self.merbs:
            if merb.target and timeh.now() < merb.eta:
                output.append(merb.print_short_info(v_target_tag=False))
        return output

    def print_all_meta(self):
        self.order('name')
        output = list()
        for merb in self.merbs:
            output.append(merb.print_meta())
        return output

    def get_all_tags(self):
        output = list()
        for tag in self.tags:
            output.append("%s\n" % tag)
        return output

    def get_all_missing(self, timezone, tag):
        self.order('window_end')
        output = list()
        now = timeh.now()
        for merb in self.merbs:
            if tag:
                if merb.check_tag(tag)and now > merb.eta:
                    output.append(merb.print_last_update(timezone))
                else:
                    continue
            elif now > merb.eta:
                output.append(merb.print_last_update(timezone))
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

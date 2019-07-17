import json
import datetime
import config
import timehandler as timeh
import npc


class Trackers:
    def __init__(self, url_json, merbs):
        self.url_json = url_json
        self.users = {}
        with open(url_json) as f:
            json_trackers = json.load(f)
        # Transform string key into key ones
        for user_id in json_trackers:
            date = datetime.datetime.strptime(json_trackers[user_id]['date'], config.DATE_FORMAT)
            self.add_tracker(int(user_id),
                             json_trackers[user_id]["what"],
                             date,
                             json_trackers[user_id]["mode"],
                             merbs)

    def add_tracker(self, user_id, what, date, mode, merbs):

        if user_id in self.users:
            return False

        tracked_merbs = list()

        single = True
        if isinstance(what, npc.Merb):
            if what.is_trackable():
                tracked_merbs.append(what)
        elif what in merbs.tags:
            single = False
            for merb in merbs.get_all_by_tag(what):
                if merb.is_trackable():
                    tracked_merbs.append(merb)
        else:
            what = merbs.get_by_name(what)
            if what.is_trackable():
                tracked_merbs.append(what)

        if not len(tracked_merbs):
            return False

        # Modify the starting time if tracked merbs are not yet in window
        tracked_merbs.sort(key=lambda merb: merb.eta)
        tracked_merbs.sort(key=lambda merb: merb.is_in_window(), reverse=True)
        if tracked_merbs[0].window['start'] > date:
            date = tracked_merbs[0].window['start']

        self.users[user_id] = {}
        if single:
            self.users[user_id]["what"] = what.name
        else:
            self.users[user_id]["what"] = what
        self.users[user_id]["date"] = date
        self.users[user_id]["mode"] = mode
        self.users[user_id]["merbs"] = tracked_merbs
        # Add the tracker to the merb object
        for merb in tracked_merbs:
            merb.add_tracker(user_id)
        return self.users[user_id]

    def get_tracker(self, user_id):
        if user_id in self.users:
            return self.users[user_id]
        else:
            return None

    def get_trackers_by_merb(self, merb):
        for tracker in self.users:
            if merb in self.get_tracked_merbs(tracker):
                return True
        return False

    def get_tracked_merb_by_user(self, user_id):
        if user_id not in self.users:
            return False

        return self.users[user_id]['merbs']

    def stop_tracker_by_user(self, user_id):
        if user_id not in self.users:
            return False
        output = self.users[user_id]
        for merb in self.users[user_id]['merbs']:
            merb.del_tracker(user_id)
        self.users.pop(user_id)
        return output

    def stop_trackers_by_merb(self, merb):
        output = list()
        for tracker in list(self.users):
            if merb in self.get_tracked_merbs(tracker):
                # Delete the merb from the tracked merbs
                self.users[tracker]['merbs'].remove(merb)
                # Delete the tracker if there are no more merbs being tracked in window
                if len(self.get_trackable_merb(tracker)) == 0:
                    output.append({tracker: {"ended": True, "info": self.get_tracker(tracker)}})
                    del self.users[tracker]
                # Else delete only the tracked merb
                else:
                    output.append({tracker: {"ended": False, "info": self.get_tracker(tracker)}})

                # delete the tracker from the merb obj
                merb.del_tracker(tracker)

        return output

    def stop_all_trackers(self):
        output = list()
        for tracker in list(self.users):
            output.append({tracker: {"ended": True, "info": self.get_tracker(tracker)}})
            del self.users[tracker]
        return output

    def get_tracked_merb_in_window(self, user_id):
        merbs = list()
        if user_id not in self.users:
            return False
        for merb in self.users[user_id]['merbs']:
            if merb.is_in_window():
                merbs.append(merb)
        return merbs

    def get_trackable_merb(self, user_id):
        merbs = list()
        if user_id not in self.users:
            return False
        for merb in self.users[user_id]['merbs']:
            if merb.is_trackable():
                merbs.append(merb)
        return merbs

    def check_tracker_by_merb(self, user_id, merb):
        if merb in self.users[user_id]['merbs']:
            return True
        return False

    def get_tracked_merbs(self, user_id):
        if user_id in self.users:
            return self.users[user_id]['merbs']
        else:
            return None

    def get_duration(self, user_id):
        if user_id in self.users:
            return timeh.countdown(self.users[user_id][self.get_tracked_merbs(user_id)], timeh.now())
        else:
            return None

    def save(self):
        save_dict = {}
        for user in self.users:
            date = datetime.datetime.strftime(self.users[user]["date"], config.DATE_FORMAT)
            save_dict[user] = {}
            save_dict[user]["what"] = self.users[user]['what']
            save_dict[user]["date"] = date
            save_dict[user]["mode"] = self.users[user]['mode']

        with open(self.url_json, 'w') as outfile:
            json.dump(save_dict, outfile, indent=4)

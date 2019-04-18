import json


class Watch:
    def __init__(self, url_json):
        self.url_json = url_json
        self.users = {}
        with open(url_json) as f:
            json_watch = json.load(f)
        # Transform strin key into key ones
        for key in json_watch:
            self.users[int(key)] = json_watch[key]


    def __str__(self):
        return self.users

    def check(self, user, merb, minute):
        if user not in self.users:
            return False
        if merb not in self.users[user]:
            return False
        if not self.users[user][merb] == minute:
            return False
        return True

    def get_single(self, user, merb):
        if user not in self.users:
            return False
        else:
            if merb not in self.users[user]:
                return False
            else:
                return self.users[user][merb]

    def get_all(self, user):
        output = {}
        if user not in self.users:
            return False
        else:
            for merb in self.users[user]:
                output[merb] = self.users[user][merb]
        return output

    def switch(self, user, merb, minutes=30, off=True):
        if user not in self.users:
            self.users[user] = {}
        if off:
            self.users[user].pop(merb, None)
        else:
            self.users[user][merb] = minutes
        self.save()

    def all_off(self, user):
        if user in self.users:
            self.users.pop(user, None)
        self.save()

    def save(self):
        with open(self.url_json, 'w') as outfile:
            json.dump(self.users, outfile, indent=2)

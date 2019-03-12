import json


class Watch:
    def __init__(self, url_json):
        self.url_json = url_json
        self.users = {}
        with open(url_json) as f:
            self.users = json.load(f)

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

    def switch(self, user, merb, minutes=30, mode="ON"):
        if user not in self.users:
            self.users[user] = {}
        if mode == "ON":
            self.users[user][merb] = minutes
        else:
            self.users[user].pop(merb, None)
        self.save()

    def off(self, user):
        if user in self.users:
            self.users.pop(user, None)
        self.save()

    def save(self):
        with open(self.url_json, 'w') as outfile:
            json.dump(self.users, outfile, indent=2)

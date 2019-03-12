import re
import json
import messagecomposer


class Helper:

    def __init__(self, json_url):
        with open(json_url) as f:
            self.help = json.load(f)

    def get_about(self):
        # if no parameter (what) is passed, return general help
        try:
            text = '\n'.join(self.help["about"])
            return messagecomposer.prettify(text, None)
        except:
            return False

    def get_help(self, what):
        if not what:
            return '\n'.join(self.help["help"])

        # find the command
        my_command = ""
        for c in self.help:
            my_command += "|" + c
        regex = r"\b(%s)\b" % my_command[1:]

        cmd = re.search(regex, what)
        # if no parameter (what) is passed, return general help
        try:
            text = '\n'.join(self.help[cmd.group(1)])
        except:
            text = '\n'.join(self.help["help"])

        return text

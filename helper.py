import os
import glob
import ntpath
import config


class Helper:

    def __init__(self, path):
        self.help = {}
        for file in glob.glob(os.path.join(path, '*.md')):
            file_name = ntpath.basename(os.path.splitext(file)[0])
            with open(file) as f:
                self.help[file_name] = f.read()

    def get_help(self, cmd):

        if cmd:
            s = "cmd_" + cmd
        else:
            s = "index"

        if s in self.help:
            return self.help[s]
        else:
            return self.help['index']

    def get_about(self):
        return self.help['about'] + "\nCLONE NAME: " + config.CLONE_NAME

    def get_released(self):
        return self.help['releases']

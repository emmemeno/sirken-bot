import config_auth as config
import timehandler as timeh
import json
from miracle import Acl
import errors
import messagecomposer
import discord


class User:

    def __init__(self, discord_user, d_roles, b_roles, guilds):

        self.discord_user = discord_user
        self.id = discord_user.id
        self.name = discord_user.name
        self.d_roles = d_roles
        self.b_roles = b_roles
        self.guilds = guilds


class DiscordRole:

    def __init__(self, guild, d_id, name):
        self.guild = guild
        self.id = d_id
        self.name = name

    def __repr__(self):
        return "DISCORD ROLE\nGUILD: %s\nID: %d\nNAME: %s" % (self.guild, self.id, self.name)


class BotRoles:

    def __init__(self, json_file_roles):
        with open(json_file_roles) as f:
            json_file = json.load(f)
        # DICT OF ROLES FOR DISCORD_ROLE_ID -> BOT ROLES
        self.bot_roles_discord = json_file["roles-discord"]
        # DICT OF BOT ROLES, WITH PERMISSIONS
        self.bot_roles = json_file["roles"]
        # LIST OF DISCORD ROLES OBJECTS
        self.discord_roles = list()

    def get_bot_roles_list(self):
        roles = list()
        for role in self.bot_roles:
            roles.append(role)
        return roles

    # Convert Discord Role In Bot Roles Using localy dict bot_roles_discord
    def convert_discord_role_into_bot_role(self, discord_id_role):
        output_role = "guest"
        for b_role, d_roles in self.bot_roles_discord.items():
            if discord_id_role in d_roles:
                output_role = b_role
        return output_role

    def add_discord_role(self, guild, role_id, role_name):
        self.discord_roles.append(DiscordRole(guild, role_id, role_name))

    def check_discord_role(self, d_input_role_id):
        for d_role in self.discord_roles:
            if int(d_input_role_id) == d_role.id:
                return d_role
        return False

    def check_bot_role(self, role):
        if role in self.bot_roles:
            return True
        else:
            return False

    # Assign a Discord Role to a Bot Role
    def assign_discord_role_to_bot_role(self, d_role, b_role):
        # check if the new discord role is present and delete it
        for key, role in self.bot_roles_discord.items():
            if d_role in role:
                role.remove(d_role)
        self.bot_roles_discord[b_role].append(d_role)
        self.save_to_json()

    def save_to_json(self):
        serialize = {"roles": self.bot_roles,
                     "roles-discord": self.bot_roles_discord
                     }
        with open(config.FILE_ROLES, 'w') as outfile:
            json.dump(serialize, outfile, indent=4)


class Auth:

    def __init__(self):
        self.discord_client = None
        self.acl = Acl()
        self.roles = BotRoles(config.FILE_ROLES)
        self.users = {}
        self.discord_guilds = list()
        self.acl.grants(self.roles.bot_roles)

    def add_discord_client(self, client):
        self.discord_client = client

    def get_single_discord_user(self, user_id):
        if int(user_id) not in self.users:
            return False
        else:
            return self.users[int(user_id)].discord_user

    def get_single_user_bot_roles(self, user_id):
        if user_id not in self.users:
            return []
        else:
            return self.users[user_id].b_roles

    def load_discord_roles(self):
        for guild in self.discord_client.guilds:
            # save a list of guilds the bot is in
            if guild not in self.discord_guilds:
                self.discord_guilds.append(guild)

            for role in guild.roles:

                self.roles.add_discord_role(guild.name, role.id, role.name)

    def reload_discord_roles(self):
        del self.roles.discord_roles[:]
        self.load_discord_roles()

    def load_discord_users(self):
        for guild in self.discord_client.guilds:
            for member in guild.members:
                d_roles = list()
                b_roles = list()
                # CHECK THE OWNER ID
                if member.id in config.CLIENT_ID_OWNER:
                    b_roles.append("owner")
                for d_role in member.roles:
                    # DISCORD ROLES
                    d_roles.append(DiscordRole(guild.name,
                                               d_role.id,
                                               d_role.name))
                    # CONVERTED BOT ROLES
                    b_roles.append(self.roles.convert_discord_role_into_bot_role(str(d_role.id)))
                    # DELETE DUPLICATES (different discord roles pointing to the same bot role)
                    b_roles = list(dict.fromkeys(b_roles))

                # if client share more than one server with the bot update only the roles, else add the user
                if member.id in self.users:
                    # discard bot roles if present
                    for old_b_role in self.users[member.id].b_roles:
                        if old_b_role in b_roles:
                            b_roles.remove(old_b_role)

                    self.users[member.id].b_roles.extend(b_roles)
                    self.users[member.id].guilds.append(guild.name)
                else:
                    self.users[member.id] = User(member, d_roles, b_roles, [guild.name])

    def reload_discord_users(self):
        self.users.clear()
        self.load_discord_users()


# DECORATOR FUNCTION
def cmd(command):
    def auth_cmd(func):
        def func_wrapper(parent_obj):

            input_user = parent_obj.input_author
            input_channel = parent_obj.input_channel
            user_roles = parent_obj.authenticator.get_single_user_bot_roles(input_user.id)
            # print("DECORATOR auth.cmd function. User_id %d Roles: %s " % (user_id, user_roles))
            # User not present?

            u_acl = parent_obj.authenticator.acl
            user_check = u_acl.check_any(user_roles, "command", command)
            # CHECK FOR CHANNEL PERMISSION
            if not isinstance(input_channel, discord.channel.DMChannel):
                channel_error_msg = "Hey %s! You are not allowed to ask me questions in %s channel\n" \
                                    "Let's talk here!" % (parent_obj.input_author.name, input_channel.name)
                if len(config.ALLOWED_CHANNELS):
                    if input_channel.id not in config.ALLOWED_CHANNELS and not input_channel.id == input_user:
                        return [{"destination": parent_obj.input_author,
                                "content": channel_error_msg,
                                'decoration': "BLOCK"}]
                if len(config.DENY_CHANNELS):
                    if input_channel.id in config.DENY_CHANNELS and not input_channel.id == input_user:
                        return [{"destination": parent_obj.input_author,
                                 "content": channel_error_msg,
                                 'decoration': "BLOCK"}]

            # CHECK FOR USER PERMISSION
            if not user_check and config.AUTHENTICATION:
                output_content = messagecomposer.prettify(errors.error_auth(command), "BLOCK")
                user_permissions = u_acl.which_permissions_any(user_roles, "command")
                output_content += messagecomposer.prettify("Commands you can use: %s" % user_permissions, "BLOCK")
                return [{"destination": parent_obj.input_author,
                         "content": output_content,
                         'decoration': "BLOCK"}]

            return func(parent_obj)

        return func_wrapper
    return auth_cmd

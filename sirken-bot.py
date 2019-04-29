import config
import auth
import logging
import logging.config
import asyncio
import discord
from discord.ext import commands
import timehandler as timeh
import messagecomposer
import inputhandler
import outputhandler
import npc
import watch
import helper
from timeit import default_timer as timer

################################################
# BACKGROUND MINUTE DIGEST : Tic every minute  #
################################################
async def minute_digest():
    tic = 60
    while True:
        await asyncio.sleep(tic)
        now = timeh.now()

        for merb in merbs.merbs:
            # update merb eta
            merb.eta = merb.get_eta()
            minutes_diff = (merb.eta - now).total_seconds() // 60.0

            for user in watch.users:
                destination = discord.utils.get(client.get_all_members(), id=user)
                if watch.check(user, merb.name, minutes_diff) and not merb.in_window():
                    await destination.send(messagecomposer.prettify(merb.print_short_info(), "CSS"))
                    logging.debug("ALARM TO %s: %s | ETA: %s | DIFF MINUTES: %s" %
                                  (user, merb.name, merb.eta, minutes_diff))


################################################
# BACKGROUND DAILY DIGEST: Tic every hour      #
################################################
async def hour_digest():
    # tic every hour
    tic = 60*60
    while True:
        await asyncio.sleep(tic)

        # Reload Roles and Users
        authenticator.reload_discord_roles()
        logger_sirken.info("Roles Reloaded")
        authenticator.reload_discord_users()
        logger_sirken.info("Users Reloaded")

        # tic only one time per day
        # now = timeh.now()
        # if int(now.hour) == config.DAILY_HOUR:
        #    merbs_print_list = merbs.get_all("CET", "countdown", limit_hours=24)
        #    if merbs_print_list:
        #        counter = len(merbs_print_list)
        #        output_content = messagecomposer.output_list(merbs_print_list)
        #        pre_content = "Good morning nerds! %d merbs are expected today, %s.\n\n" %\
        #                      (counter, timeh.now().strftime("%d %b %Y"))
        #        post_content = "\n{Type !hi to start to interact with me}\n"
        #        raw_output = out_h.process(pre_content + output_content + post_content)
        #        for message in raw_output:
        #            await send_spam(messagecomposer.prettify(message, "CSS"), config.BROADCAST_DAILY_DIGEST_CHANNELS)


def setup_logger(name, log_file, level=logging.INFO):

    formatter = logging.Formatter('[%(asctime)s] - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


########
# MAIN #
########
if __name__ == "__main__":

    # Generic Sirken-Bot file logger
    logger_sirken = setup_logger('Sirken-Bot', config.LOG_FILE)

    # Input file logger
    logger_input = setup_logger('Input', config.LOG_INPUT_FILE)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
    })

    # Initialize the Bot
    t_start = timer()
    client = commands.Bot(command_prefix="!")  # Initialise client bot
    t_end = timer()
    logger_sirken.info("Loading Bot. Done in (%s)" % (round(t_end-t_start, 5)))

    # Initialize Auth
    authenticator = auth.Auth(client)

    # Initialize Merbs List
    t_start = timer()
    merbs = npc.MerbList(config.FILE_ENTITIES,
                         config.FILE_TIMERS,
                         config.FILE_TARGETS,
                         config.DATE_FORMAT,
                         config.DATE_FORMAT_PRINT)
    merbs.order()
    t_end = timer()
    logger_sirken.info("Loading Merbs. Done in %s seconds" % (round(t_end-t_start, 5)))

    # Load Helper
    t_start = timer()
    helper = helper.Helper(config.HELP_DIR)
    t_end = timer()
    logger_sirken.info("Loading Help. Done in %s seconds" % (round(t_end-t_start, 5)))

    # Load Watcher
    t_start = timer()
    watch = watch.Watch(config.FILE_WATCH)
    t_end = timer()
    logger_sirken.info("Loading Watcher. Done in %s seconds" % (round(t_end-t_start, 5)))

    # Initialize Output Handler
    t_start = timer()
    out_h = outputhandler.OutputHandler(config.MAX_MESSAGE_LENGTH)
    # Initialize Input Handler
    in_h = inputhandler.InputHandler(authenticator, merbs, helper, out_h, watch)
    t_end = timer()
    logger_sirken.info("Loading IO. Done in %s seconds" % (round(t_end-t_start, 5)))

    @client.event
    async def on_ready():
        logger_sirken.info("Sirken Bot is online and connected to Discord")
        # Load Discord Roles
        t_start = timer()
        authenticator.load_discord_roles()
        t_end = timer()
        logger_sirken.info("Loading Discord Roles. Done in %s seconds" % (round(t_end - t_start, 5)))
        t_start = timer()
        authenticator.load_discord_users()
        t_end = timer()
        logger_sirken.info("Loading Discord Users. Done in %s seconds" % (round(t_end - t_start, 5)))


    @client.event
    async def on_message(message):
        # Skip self messages
        if message.author == client.user:
            return

        raw_output = in_h.process(message.author, message.channel, message.content)

        if raw_output:
            # split the output if too long
            output_message = out_h.process(raw_output["content"])
            for message in output_message:
                await raw_output["destination"].send(message)
                if raw_output['broadcast']:
                    await send_spam(message, raw_output['broadcast'])

            # send PM Alerts
            if 'merb_alert' in raw_output:
                await send_pop_alerts(raw_output['merb_alert'], raw_output["content"])
            # send EQ Alerts
            if 'earthquake' in raw_output:
                await send_eq_alert(raw_output['earthquake'])

    # Send Spam to Broadcast Channel
    @client.event
    async def send_spam(message, channels):
        for channel in channels:
            destination = client.get_channel(channel)
            await destination.send(message)

    # Send Earthquake Messages
    @client.event
    async def send_eq_alert(author):
        # for user in watch.users:
        #   destination = discord.utils.get(client.get_all_members(), id=user)
        #    await client.send_message(destination,
        #                              messagecomposer.prettify("%s BROADCAST: Minions gather, their forms appearing"
        #                                                       " as time and space coalesce." % author, "CSS"))
        #    logging.info("EARTHQUAKE!")
        pass

    # Send Pop Message
    @client.event
    async def send_pop_alerts(merb: npc.Merb, message):
        # for user in watch.users:
        #    destination = discord.utils.get(client.get_all_members(), id=user)
        #    if merb.name in watch.users[user]:
        #        await client.send_message(destination, messagecomposer.prettify(message, "CSS"))
        #        logging.info("SEND ALERT. %s pop TO: %s" % (merb.name, user))
        pass

    # Run the Bot
    client.loop.create_task(minute_digest())
    client.loop.create_task(hour_digest())
    client.run(config.DISCORD_TOKEN)

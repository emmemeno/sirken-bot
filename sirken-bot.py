import config
import logging
import logging.config
import asyncio
import discord
from discord.ext import commands
import timehandler as timeh
import npc
import watch
import messagecomposer
import trackers
import embed_message
import helper
from sirken_commands import SirkenCommands
from timeit import default_timer as timer


##############
# LOGGER SETUP
##############
def setup_logger(name, log_file, level=logging.INFO):

    formatter = logging.Formatter('[%(asctime)s] - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


##################
# TIC EVERY MINUTE
##################
async def minute_digest():
    tic = 60
    while True:
        await asyncio.sleep(tic)
        now = timeh.now()

        for merb in merbs.merbs:
            # update merb eta
            merb.eta = merb.get_new_eta()
            minutes_diff = (merb.eta - now).total_seconds() // 60.0

            # broadcast the alarm 30 minutes before a target spawns
            if merb.target and minutes_diff == 30:
                print_info = merb.print_short_info(v_trackers=True) + "\n"
                message = config.TAG_ALERT + "\n" + messagecomposer.prettify(print_info, "RED")
                try:
                    await client.get_channel(config.BROADCAST_CHANNEL).send(message)
                    logger_sirken.info(f"Broadcast alarm sent for {merb.name}")
                except Exception as e:
                    logger_sirken.error(f"Broadcast alarm not sent! Error: {e}")

            # send a pm to watchers
            for user in watch.users:
                destination = discord.utils.get(client.get_all_members(), id=user)
                if watch.check(user, merb.name, minutes_diff) and not merb.is_in_window():
                    try:
                        await destination.send(messagecomposer.prettify(merb.print_short_info(), "CSS"))
                        logging.info("PM Alarm sent to %s: %s | ETA: %s | DIFF MINUTES: %s" %
                                    (user, merb.name, merb.eta, minutes_diff))
                    except Exception as e:
                        logger_sirken.error(f"PM Alarm not sent! Error: {e}")

        # UPDATE EMBED TIMERS
        try:
            await embed_timers.update_message(client, merbs, trackers)
            # logger_sirken.info("Embed timers updated.")
        except Exception as e:
            logger_sirken.error(f"Embed timers not updated! Error: {e}")



################
# TIC EVERY HOUR
################
async def hour_digest():
    # tic every hour
    tic = 60*60
    while True:
        await asyncio.sleep(tic)

        # Reload Roles and Users
        config.authenticator.reload_discord_roles()
        logger_sirken.info("Roles Reloaded")
        config.authenticator.reload_discord_users()
        logger_sirken.info("Users Reloaded")

        # Reload Emojii
        embed_timers.load_emojii(client)


######
# MAIN
######
if __name__ == "__main__":

    # Generic Sirken-Bot file logger
    logger_sirken = setup_logger('Sirken-Bot', config.LOG_FILE)

    # Input file logger
    logger_io = setup_logger('Input Output', config.LOG_IO_FILE)

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
    config.authenticator.add_discord_client(client)

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

    # Load Trackers
    t_start = timer()
    trackers = trackers.Trackers(config.FILE_TRACKERS, merbs)
    t_end = timer()
    logger_sirken.info("Loading Trackers. Done in %s seconds" % (round(t_end-t_start, 5)))

    # Initialize Sirken Commands
    sirken_cmds = SirkenCommands(client, config.authenticator, merbs, helper, watch, trackers)
    t_end = timer()
    logger_sirken.info("Loading IO. Done in %s seconds" % (round(t_end-t_start, 5)))

    # Initialize Embed timers
    embed_timers = embed_message.EmbedMessage(config.TIMERS_CHANNEL, "**TARGET TIMERS**", "")

    ##############
    # BOT IS READY
    ##############
    @client.event
    async def on_ready():
        logger_sirken.info("Sirken Bot is online and connected to Discord")
        # Load Discord Roles
        t_start = timer()
        config.authenticator.load_discord_roles()
        t_end = timer()
        logger_sirken.info("Loading Discord Roles. Done in %s seconds" % (round(t_end - t_start, 5)))
        t_start = timer()
        config.authenticator.load_discord_users()
        t_end = timer()
        logger_sirken.info("Loading Discord Users. Done in %s seconds" % (round(t_end - t_start, 5)))
        # LOAD EMBED
        embed_timers.load_emojii(client)
        try:
            await embed_timers.update_message(client, merbs, trackers)
            logger_sirken.info("Embed timers updated.")
        except Exception as e:
            logger_sirken.error(f"Embed timers not updated! Error: {e}")
        print("BOT READY: %s" % config.DISCORD_TOKEN)

    ####################
    # A MESSAGE INCOMING
    ####################
    @client.event
    async def on_message(input_message):
        # Skip self messages
        if input_message.author == client.user:
            return

        t_input_process_start = timer()
        response_messages = sirken_cmds.process(input_message)
        t_input_process_end = timer()

        # Do nothing if there are no responses
        if not response_messages:
            return

        # calculate the processing time and print on log
        processing_time = round(t_input_process_end - t_input_process_start, 5)
        logger_io.info("INPUT: %s - %s (%s) " % (input_message.author.name, input_message.content, processing_time))

        # Loop the output messages list and cut messages too long for discord
        output_messages = list()
        for raw_message in response_messages:
            if len(raw_message['content']) > config.MAX_MESSAGE_LENGTH:
                for trunk in messagecomposer.message_cut(raw_message['content'], config.MAX_MESSAGE_LENGTH):
                    output_messages.append({'destination': raw_message['destination'],
                                            'content': trunk,
                                            'decoration': raw_message['decoration']})
            else:
                # if length is under limit, just copy the message in the output list
                output_messages.append(raw_message)

        for output_m in output_messages:
            # Send the decorated messages
            await output_m['destination'].send(messagecomposer.prettify(output_m['content'], output_m['decoration']))
            logger_io.debug("OUTPUT: %s - %s" % (output_m['destination'], output_m['content']))


    ###########################
    # Run the Bot and two tasks
    ###########################
    client.loop.create_task(minute_digest())
    client.loop.create_task(hour_digest())
    client.run(config.DISCORD_TOKEN)

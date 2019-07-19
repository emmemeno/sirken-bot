import config
import discord
import timehandler as timeh


class EmbedMessage:
    def __init__(self, channel_id, title, description):
        self.title = title
        self.description = description
        self.channel_id = channel_id
        self.channel = None
        self.message = None
        self.users = None

    async def get_last_message(self, client):
        self.channel = client.get_channel(self.channel_id)
        history = await self.channel.history(limit=1, oldest_first=True).flatten()
        if len(history):
            self.message = history[0]

    def compose_timers_message(self, merbs, trackers):
        embed_timers = discord.Embed(title=self.title, description=self.description, color=0x444444)
        # field_content = "__in window__ for the next **8 hours and 29 minutes**\n"
        # field_content += "Active Trackers: `Cat` `Dog` `Hot` `myself`"
        # field_content2 = "window will open in 3 hours and 59 minutes\n"
        #
        # embed_timers.add_field(name="Trakanon", value=field_content, inline=True)
        # embed_timers.add_field(name="Vulak", value=field_content2, inline=True)
        merbs.order('eta')
        counter_all = counter_in_window = 0
        for merb in merbs.merbs:

            if merb.has_eta() and merb.is_target() and counter_all < 24:
                counter_all = counter_all + 1
                field_content = ""
                name_content = merb.name

                if merb.pop > merb.tod and timeh.now() < merb.window['start']:
                    if not timeh.halfway_to_start_window(merb):
                        name_content = config.EMOJII_POPPED + "  " + name_content
                        field_content += " popped %s ago\n" % timeh.countdown(merb.pop, timeh.now())
                    else:
                        field_content += "window roughly opens in %s\n" % timeh.countdown(timeh.now(), merb.eta)
                else:
                    if merb.is_in_window():
                        counter_in_window = counter_in_window + 1
                        name_content = config.EMOJII_WINDOW_OPEN + "  " + name_content
                        field_content += " *__in window__* for the next "
                    else:
                        field_content += "window opens in "

                    field_content += timeh.countdown(timeh.now(), merb.eta) + "\n"

                if merb.plus_minus:
                    active_trackers = merb.get_trackers()
                    if active_trackers:
                        field_content += "Active trackers: "
                        for tracker in active_trackers:
                            tracker_name = str(tracker)
                            try:
                                tracker_name = config.authenticator.users[tracker].name
                            except:
                                pass
                            mode = trackers.get_tracker(tracker)['mode']
                            field_content += tracker_name
                            if mode:
                                field_content += " (%s)" % mode
                            field_content += " - "
                        field_content = field_content[:-3]
                        field_content += "\n"
                    else:
                        field_content += ""
                field_content += "-"

                embed_timers.add_field(name=name_content, value=field_content, inline=False)

        footer = "%d total, %d in window.\nLast update %s UTC" % (counter_all, counter_in_window, timeh.now().strftime(config.DATE_FORMAT_PRINT))
        embed_timers.set_footer(text=footer)

        return embed_timers

    async def update_message(self, client, merbs, trackers):
        # Get the last message id from the channel
        await self.get_last_message(client)
        # Create a new timers message
        message = self.compose_timers_message(merbs, trackers)
        if not self.message:
            # print("Message ID not found. Creating a new one")
            await self.channel.send(embed=message)
        else:
            # print("Updating Message ID %d" % self.message.id)
            await self.message.edit(embed=message)
        # message_content = compose_embed_timers_message(merbs)
        #
        # if embed_timers_message:
        #     await embed_timers_message.edit(embed=message_content)
        # else:
        # await channel.send(embed=embed_timers_message)
# Sirken Bot
###### They say I give *respawn times*.

Interactive discord bot who stores and updates times of death, pops and watch merbs and their eta

### LIST OF COMMANDS
```
  [!about]        - About Sirken Bot
  [!help]         - Show this help
  [!get]          - Show merbs due to spawn
  [!tod]          - Update the ToD of a Merb
  [!pop]          - Update the pop time of a Merb
  [!track]        - Track a Merb
  [!missing]      - Show a list of outdated merbs
  [!earthquake]   - Omg omg omg (be careful, will reset all pop date/time!)
  [!watch]        - Keep an eye on your merbs
  [!merbs]        - List name and aliases of supported Merbs
  [!target]       - Set a merb target
  [!roles]        - Print Bot roles
  [!setrole]      - Convert a discord role to a bot role
  [!users]        - Print Users

```
To see a specific help type !help command:
```
!help get
```
```
!help tod
```
```
...
```

### RELEASES
##### 1.0 aka Killing the Spam
```
- Added the Target Timers widget in the brand new (read-only) timer channel, updated every minute.
- The tracking system is now based on sessions to give more accurate tracking times. This is how it works:
    - You can have only 1 active session at a time
    - A session can be a single merb or a tag
    - You can stop the session with just {!track stop} command...
    - ...or when all your tracked merbs pop.
    - If merb(s) is not in window yet, starting track time is set to merb(s) window opening.
- Added the BP option on !pop command. This is added to prevent chaotic situations where merbs spawn close each other and a batphone is not needed.
  So now if you want to batphone a merb, use the keyword `BP`:
  ex. {!pop vulak bp}
- Added the {!track info} command to show the status of your tracking session.
- Added the {!watch info} command to show merbs you are watching
- Removed the daily digest. You can still get merbs in the next 24 hours with the new command {!get today}
- The allow/deny channel system is in. Interacting with the bot is now restricted to these channels: raid-chat, asky-gynok, sleepers-tomb, raid-strategies
  Again, 95% of times you should interact with the bot via Direct Messages.
  Gynok is also connected to a micro explosive located back on your neck. Writing in the wrong channel will activate it causing your skull to explode (experimental).
- All the important messages (tods, pops, tracks, targets, windows opening alerts etc.) will be broadcasted, in different colors, to gynok-horn channel. This is a read-only channel.
- Added new aliases: Shady, Doze, Fay, Gozz, Kozz, Lady M, Lady N, MotG, Sniffles, Telk, Trak, Velk
- Added new tags: dn, swc
```

##### 0.8 aka Paranoid Android
```
- Added a RBAC: Now Sirken will parse discord servers roles converting them to bot roles. That means if you dont have
  the right permission you will not be able to use the relative command.
- added !users and !roles commands, only for adults
- added !target command. Thank you Nareb for the suggestion, it's a very nice addition!
    ex.: !target Lord Bob 
         !target Lord Bob off
    - Target merb will be autoswitch off when its tod is updated. 
    - To list targets: !get targets
- Added a more sophisticated logging system
- Changed the !help outputs to be more verbose and (hopefully) clearer.

```
##### 0.73
```
- Fixed a future tod/pop date bug. Now when you use a time that's in the future, yesterday is assumed.
  This typically happens when you update a tod with hh:mm syntax after your local midnight.
- Added the yesterday parameter to !tod/!pop commands. This will force to use yesterday when hh:mm is used.
  Example: !tod Lord Bob 23:50 yesterday
- Added support to British colonies aka 12h time format
  Example: !tod Lord Bob 11:50pm
- Added "around" word as an "approx" alias
  Example: !tod Lord Bob around 12:00 am
```
##### 0.7
```
Sirken Bot version 0.7 aka "velious" is live: everything since now will be not classic, even the solved bugs :)
-  Added tags! thank you @Tarscales#4518 for your precious help!
   - Tags used: kael, ntov, wtov, triplets, st, vp
   - Usage example: {!get ntov}
-  Now Sirken is a little smarter and will interpret better your intentions, hopefully!
   - Example: {!get vilepang}
-  removed !list command. to get all merbs due to spawn, type {!get all}
-  removed !windows command. to get all merbs in window type {!get windows}
-  minor bug fixes
-  some aesthetic changes
```

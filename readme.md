# Sirken Bot
###### They say I give *respawn times*.

Interactive discord bot who stores and updates times of death, pops and watch merbs and their eta

### LIST OF COMMANDS
```
  [!help]         - Show the help
  [!get]          - Show the status of a Merb
  [!tod]          - Update the ToD of a Merb
  [!pop]          - A Merb is popped
  [!earthquake]   - omg omg omg (be careful, will reset all pop date/time!)
  [!watch]        - Keep an eye on your merbs
  [!merbs]        - List name and aliases of supported Merbs
  [!about]        - About Sirken Bot
```

### !get
Print all merbs due to spawn:
```
!get all
```
Print all merbs in window
```
!get windows
```
Print all merbs of the specified tag
```
!get ntov
 ```            
 Get a specified merb
 ```
!get Lord Bob
```
Get more info about a specified merb
```
!get Lord Bob info
```

### !tod & !pop
With these commands you will update respectively time of death and pop time of a single merb.
Pop times are used to calculate merb eta only if newer than tod.
Both commands share the same syntax.

Simplest way to update a merb (to current date)
```
!tod Lord Bob now
```
Updates some minutes ago
```
!tod Lord Bob 10 minutes ago
```
Updates to a specified time. If time is in the future, yesterday is assumed
```
!tod Lord Bob 14:01
```
Use different timezones
```                                   
!tod Lord Bob 14:01 yesterday est
```
Use the 12hour am/pm time format
```
!tod Lord Bob 02:01pm pst
```
Force the date to yesterday
```                         
!tod Lord Bob 02:01am yesterday
```
Full date/time
```
!tod Lord Bob 2019-04-20 12:01a.m.
```
```
!tod Lord Bob 2019-04-19 05:00PM pst
```

### !earthquake
Updates all merbs pop times to the specified time. the time format is the same used for !tod and !pop
```
!earthquake now
```
```
!earthquake 12:59am
```

### !watch
Keep a look on your merbs and be alerted before their spawns/window opens.

Print all watched merbs
```
!watch
```
Watch a specified merb and be alerted 30minutes before his eta
```
!watch Lord Bob
```
Be alerted one hour before eta
```
!watch Lord Bob 60
```
Switch off a watcher
```
!watch Lord Bob off
```
Switch off all watchers
```
!watch off
```

### !merbs
Prints privately a crude list of merbs/alias/tags
```
!merbs
```

### RELEASES
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

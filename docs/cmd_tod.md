-
**!TOD**
-
This command updates the time of death, used to calculate the eta of a merb.
-
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
!tod Lord Bob 14:01 est
```
Use the 12hour am/pm time format
```
!tod Lord Bob 02:01pm pst
```
Force the date to yesterday
```
!tod Lord Bob 02:01am yesterday
```
Not sure about the time
```
!tod Lord Bob around 14:00
```
Full date/time
```
!tod Lord Bob 2019-04-20 12:01a.m.
```
```
!tod Lord Bob 2019-04-19 05:00PM pst
```
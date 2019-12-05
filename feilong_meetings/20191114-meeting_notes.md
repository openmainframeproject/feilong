# 2019/11/14 Feilong project meeting

## Attendees
Mike Friesenegger  
Johan Schelling  
Vincent Terrone  


## Agenda topics
- Introduction of new attendees
- Update on CI/CD infrastructure effort
- List of features to add
- Update on how-to access z/VM resource effort
- Discussion about core infrastructure badge effort

## Meeting Notes

### Introduction of new attendees
- No new attendees

### Update on CI/CD infrastructure effort
- Ji Chen and Andrew Grimberg not on call

### List of features to add
- Direct attached scsi for the root filesystem
  - Johnan and ICU team had a discussion with Ji Chen how to do this
  - Will share Nick's (ICU intern) design with Ji Chen
    - ICU will share design with Feilong for community input
  - Believe changes are needed to create, deploy and start guest routines
  - An interesting discussion about how to collect wwpn to use
    - One idea is to use a rexx script
    - Would like community input: Are there concerns with introducing code exits to rexx and assembler or better to use existing APIs?
- Comments from Vincent about his CMA (Cloud Management Appliance) experience
  - No cinder driver available for storage subsystem
  - Experienced smapi issues which required weekly restarts

## Next meeting agenda topics
- Update on CI/CD infrastructure effort
- Update on how-to access z/VM resource effort
- Discussion about core infrastructure badge effort

# 2019/09/19 Feilong project meeting

## Attendees
John Mertic  
James Vincent  
Johan Schelling - ICU IT  
Len Santalucia  
Ingo Adlung - IBM  
Ji Chen
Mike Friesenegger

## Agenda topics
- Introductions
- Discuss not letting this project get mired in the "weeds"
- Post meeting notes
- Discuss moving CI/CD infrastructure
- Information how ICU IT is using z/VM Cloud Connnector

## Meeting Notes

### Introductions
- Asked new attendees to introduce themselves

### Discuss not letting this project get mired in the "weeds"
- Question was asked if the focus/direction of the project just on cloud connector
  - The consensus is that the z/VM Cloud Connnector is the focus
  - But the project needs to stay open to other thoughts about future APIs enhancements

###  Post meeting notes
- **TO DO:** ~~Mike and James to discuss what this is with John~~

### Discuss moving CI/CD infrastructure
- **TO DO:** ~~John Mertic will take the lead to start a conversation for next meeting~~

### Information how ICU IT is using z/VM Cloud Connnector
- Presentation given by Johan
- City of the Hague wanted to move Oracle DBs to IBM Z
- Interested in move to a cloud situation using a self-service portal
  - Looked at zoom, z/VM Wave and z/VM Cloud Connnector
  - Chose Cloud Connector
      - Call api to create vm guest was seen as a benefit
      - Added automation of VM guest creation from adding entry in CMDB
      - Not using Openstack
      - Customer is happy
      - Currently provisioning production/dev/test systems
      - some bugs found, reported and fixed
      - Would like to see enhancements
- Possible enhancement to rally around
  - Hague is using Hitachi g800 systems
  - No ECKD storage
  - Using scsi for z/VM and Linux guests
  - Emulated ECKD devices for OS disks
      - Seen poor performance with emulated ECKD disks
  - Using scsi disks for Oracle DBs
  - Would like to change APIs to add support for scsi disks
    - Has an intern diving into the code - Nick
  - Already shared the idea in the Feilong mailing list
  - Ji chen commented that the api is close to 2/3 done
      - The z/VM CC focuses on creating guest
      - Has not been a focus of ZCC because it has relied on cinder (openstack)

## Next meeting agenda topics
- Core infrastructure badge effort
- LF CI/CD infrastructure discussion
    - This discussion should not happen on October 3 because Chinese holiday  

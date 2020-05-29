# 2020/05/14 Feilong project meeting

## Attendees
- Len Santalucia
- Daniel Pono Takamori
- James Vincent
- Johan Schelling
- Vinnie Terrone
- Ji Chen
- Hai Jie Wu
- Mike Friesenegger

## Agenda topics
- Discuss the Feilong s390x infrastructure diagram

## Meeting Notes

### Discuss the Feilong s390x infrastructure diagram
- Instructions how to open the diagram
  - Download [Feilong-s390x_Infrastructure.drawio](https://github.com/openmainframeproject/python-zvm-sdk/blob/master/feilong_meetings/Feilong-s390x_Infrastructure.drawio) to your local system
  - Open [draw.io](Feilong-s390x_Infrastructure.drawio) in a browser
  - Select _Open Existing Diagram_
  - Find the Feilong-s390x_Infrastructure.drawio file that was previously downloaded
- The three CI/CD VMs are setup
  - Accessible via zowe
  - Vinnie will provide documentation to access
  - Hai Jie and CI/CD team will attempt to connect and configure with Github action
- OS disk (mod-9) plus mod-27 extra disk
  - Pono thinks only 1gb is needed
  - Pono will test to confirm
- Two second level zVM guests are available
  - Maint access to the second level only
  - No Linux VM in second level
    - A developer will need to install Linux sdk vm
  - Talk with IBM to find out how to easily duplicate second level z/vm
    - It is possible to use zpro to clone z/vm
    - Len will ask James Vincent to help with getting zpro setup once the Vicom environment is running
    - Goto to Velocity for a zpro demo
- Agreement to use feilong mailing list for communicating progress and issues

## Next meeting agenda topics
- Mike Friesenegger will present a simple demonstration of python-zvm-sdk in action

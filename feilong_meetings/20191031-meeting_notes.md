# 2019/10/31 Feilong project meeting

## Attendees
James Vincent  
Vincent Terrone  
Mike Friesenegger  
Andrew Grimberg  
Len Santalucia  
Ji Chen  
Ingo Adlung   

## Agenda topics
- Introduction of new attendees
- Update on core infrastructure badge effort
- Access to z/VM environment for testing/development
- CI/CD infrastructure to Linux Foundation
- List of features to add

## Meeting Notes

### Introduction of new attendees
- Len is the Vicom Infinity CTO and sits on the OMP board
- Ingo is the IBM Chief Architect and CTO for Z and LinuxONE and is on the OMP technical steering committee

### Update on core infrastructure badge effort
- Nothing to report
- **TODO:** Everyone please review for a discussion next meeting
  - https://bestpractices.coreinfrastructure.org/en

### Access to z/VM environment for testing/development
- Discussion about hot to access environments
  - Vicom Infiinity
      - Send Len an email with request
      - Vincent will provide a second level guest
      - Vicom has a ZR1
    - Velocity Software
      - Can submit request on Velocity website
      - Barton will ask James to create a second level VM
      - zPro is being used to provision the guest
        - Guest wll have a short life span but James can work to lengthen this
- **TO DO:** Create a how-to document that explains using Vicom and Velocity resources
  - Mike will start the creating a how-to with Vincent and James

### CI/CD infrastructure to Linux Foundation
- LF CI/CD team requires budget authority for this effort
- LF CI/CD team will need to do a discovery
- Andrew will connect John Mertic to confirm this effort
  - **TO DO:** Andrew ill send a list of questions to Ji Chen for discovery
- Link to CI/CD LF environment information from previous meeting
  - https://docs.releng.linuxfoundation.org
- LF does not have access to a Z
  - LF will connect to an external Z infrastructure
  - Possibly use marist resources
- Andrew Grimberg <agrimberg@linuxfoundation.org> is available to answer questions about LF CI/CD environment and requirements

## Next meeting agenda topics
- Update on CI/CD infrastructure effort
- Update on how-to access z/VM resource effort
- List of features to add
- Discussion about core infrastructure badge effort

# 2019/10/03 Feilong project meeting

## Attendees
John Metric
Len Santalucia
Andrew Grimberg - LF Release Eng Msanager
Mike Friesenegger

## Agenda topics
- Introductions
- LF CI/CD infrastructure
- Core infrastructure badge effort discussion
- Are we aware of others using CC that should be invited to Feilong project meetings
  - Cloud Connector was being built as a replacement for the  Cloud Management Appliance (CMA)
- Build list of features to add   

## Meeting Notes

### Introductions
- Andrew introduced himself and his role

### LF CI/CD infrastructure
- Andrew presented info about the LF CI/CD team
- Currently 12 CI/CD projects that his team manages
- Documentation about infrastructure - https://docs.releng.linuxfoundation.org
  - graphics provide a good introduction to infrastructure configuration
- gerrit/jenkins setup is default
  - Can do github but may require additional scripting
- Andrew asked a number of questions to the group
  - Does the CI/CD touch a z system
    - Mike said yes but Ji Chen can provide more details
    - If something is not in the LF build cloud then someone in the Feilong project must troubleshoot and manage connected instances
      - LF CI/CD team will troubleshoot job issues
      - These types issues need at least one call which typically is an hour
    - Len offered Vicom mainframe to be used for OMP projects
  - Is the intent to move zVM CC to gerrit?
    - The project was hosted on Gerrit before being moved to OMP github
      - Gerritt was being mirrored to github
    - Can move to github but weaker APIs then Gerrit
- There are specific requirements to move to LF CI/CD
  - DCO is required on every commit
      - All commits must need this to preserve history
      - LF provides a DCO checker
        - pip install of lftools
        - ```lftools --help``` for details
        - quick check is sufficient

## Next meeting agenda topics
- Core infrastructure badge effort discussion
- Are we aware of others using CC that should be invited to Feilong project meetings
  - Cloud Connector was being built as a replacement for the  Cloud Management Appliance (CMA)
- Build list of features to add   

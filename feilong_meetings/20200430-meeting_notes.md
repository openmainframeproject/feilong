# 2020/04/30 Feilong project meeting

## Attendees
- John Mertic
- Vinnie Terrone
- Daniel Pono Takamori
- Len Santalucia
- Dong JV Ma
- Ji Chen
- Johan Schelling

## Agenda topics
- Status of Vicom Infinity infrastructure
- Discussion on the Z infrastructure for CI/CD infrastructure
- Update on how-to access second-level VM for developers

## Meeting Notes

### Status of Vicom Infinity infrastructure
- Discussion led by Vinnie
- Created two second level VMs
  - z/vm 7.1
  - accessible via zowe 3270
- Vinnie asked what VMs are needed for CI/CD
  - 3 first level Ubuntu images are needed
    - Refer to 20200416 meeting notes for VM details
  - 2 VMs already built
  - Vinnie will build the remaining VM
- Vinnie asked what second level VMs are needed for developer environments
  - Currently the second level z/VM does not have any VM guests created
  - No decision was made whether the second level z/VM should have a pre-built Linux VM
  - Vinnie commented that cloning a second level z/VM is difficult
- Discussion about 3270 and ssh access requirements for CI/CD and developer environments
  - First level VMs for CI/CD needs only ssh access
  - Second level z/VM environments need 3270 and ssh access
  - Vinnie asked to send a list of people who need access
    - Name of person
    - 8 characters for username
    - List of people for each environment
      - Daniel Pono Takamori (CI/CD)
      - Dong Ma (CI/CD)
      - Hai Jie Wu (CI/CD)
      - Ji Chen (Developer environment)
      - Mike Friesenegger (Developer environment)
  - Vinnie asked for information about following resources for second level z/VM environments
      - Number of ip addresses
      - Amount of storage
        - Vicom is using mod-9s for storage
        - FCP based storage is not available today

### Discussion on the Z infrastructure for CI/CD infrastructure
- From April 21, below are the meeting notes of CI/CD discussion between LF team and IBM China Team:
    1. Dong Ma introduced the currently CI/CD environment inside IBM for Feilong project
    1. LF team shared the CI POC for Feilong project, the POC have enabled the Github action to run the tox job for Feilong project, https://github.com/pono/python-zvm-sdk/runs/603727735?check_suite_focus=true, this is works for the CI part, the open question is how to connect to the Z infrastructure in Vicom Infinity
    1. Next step action.
     - IBM China Team will follow up with Vicom Infinity team to finalize the Z infrastructure
     - LF team will evaluate how to connect to the Vicom Infinity Z infrastructure if it is ready
     - LF team will POC the api test for the PYPI
- John Mertic created https://github.com/openmainframeproject/tac/issues/99 to keep the communication open and aware for other projects looking to use this.

### Update on how-to access second-level VM for developers
- Did not discuss how-to access the second level z/VM for developers

## Next meeting agenda topics
- Discuss the [Feilong s390x infrastructure diagram ](./Feilong-s390x_Infrastructure.drawio)
- Mike Friesenegger will present a simple demonstration of python-zvm-sdk in action

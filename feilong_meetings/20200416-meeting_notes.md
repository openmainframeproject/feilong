# 2020/04/16 Feilong project meeting

## Attendees
- Johan Schelling
- Mike Friesenegger
- Dong JV Ma
- Hai Jie DC Wu
- Vinnie Terrone
- Len Santalucia

## Agenda topics
- Discussion on the Z infrastructure for CI/CD infrastructure
- Update on how-to access second-level VM for developers

## Meeting Notes

- problems getting into Zoom
- issues with joining via mobile phone
  - *6 to mute when joining via phone

### Discussion on the Z infrastructure for CI/CD infrastructure
- These will be first level guests on z/vm 6.4
- May be possible to open ports or use ssh bastion host via web browser
- To send code to the guests then vpn is required
- Hai Jie has sent the requirements and OS information
    - z/VM: Version 6.4 or 7.1
  - Linux Distro: Ubuntu 18.04 LTS s390x
    - http://cdimage.ubuntu.com/releases/18.04/release/
  - Required Linux VMs:
    - SDK REST API FVT ----- 1 zVM Linux virtual machine （4 shared IFL, 8g RAM, 30G disk）
    - BVT1#----- 1 zVM Linux virtual machine（4 shared IFL, 8g RAM, 30G disk）
    - BVT2#(Python3)----- 1 zVM Linux virtual machine（4 shared IFL, 8g RAM, 30G disk）
  - Other requirements:
    - Linux Guest on top of z/VM, not 2nd layer VMs.
    - z/VM Pre-requirement configuration: https://cloudlib4zvm.readthedocs.io/en/latest/quickstart.html#pre-requirements
    - Out bound connection to Github, Python PIP, Linux repo.
    - The z/VM which install the Linux guest VM should have reserved CPU/Mem/Disk resources, the test will dynamically deploy/delete guest VMs during test executions.
    - It is better if 3 VMs can be deployed into different z/VM systems, but not mandatory.
    - Need to work out a solution for inbound connection from github.com for Github Actions triggers.
    - Use bastion to access the Linux VMs should OK
    - For external to internal, vpn will be needed to access via Github Actions

### Update on how-to access second-level VM for developers
- Access through Zowe for 3270
- ssh access will be required
- AI: Johan will have his admin contact Vinnie to review
- AI: Mike setup web session with Vinnie to show python-zvm-sdk in action

## Next meeting agenda topics
- Discussion on the Z infrastructure for CI/CD infrastructure
- Update on how-to access second-level VM for developers

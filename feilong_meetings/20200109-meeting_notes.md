# 2020/01/09 Feilong project meeting

## Attendees
John Mertic  
James Vincent  
Len Santalucia   
Vincent Terrone  
Hai Jie Wu  
Ji Chen  

## Agenda topics
- Introduction of new attendees  
- Update on CI/CD infrastructure effort  
- Update on how-to access z/VM resource effort  
- Discussion about core infrastructure badge effort  

## Meeting Notes

### Introduction of new attendees
- Hai Jie Wu
  - Working at IBM on the CI/CD infrastructure for Feilong

### Update on CI/CD infrastructure effort
- Invited Zowe CI/CD team lead (Jack-Tiefeng Jia) and Andrew Grimberg from LF
- Two topics discussed
  - Zowe has setup Jenkins
  - Zowe has Z resources available
- Goal to see if Feilong can use the Zowe Jenkins infrastructure
  - Jack agreed but needs to speak with his management
  - Change hostname of the Jenkins server to make name more general
  - Some potential security concerns that where discussed
- It is not possible for Feilong to use Zowe Z resources
  - Action item is to find Z reosources for Feilong testing
  - Possible resources from VCU in 2 - 3 months
  - Provide a list of requirements for other organizations
    - Item #1 below will be handled by the Zowe Jenkins server  
      **CI/CD environment needed for Feilong project:**
      1. Jenkins server ----- 1 Linux server
      2. SDK REST API FVT ----- 1 zVM Linux virtual machine （4 shared IFL, 8g RAM, 30G disk） RHEL7.x
      3. BVT ----- 1 zVM Linux virtual machine（4 shared IFL, 8g RAM, 30G disk） RHEL7.x
      4. Python3 BVT ----- 1 zVM Linux virtual machine（4 shared IFL, 8g RAM, 30G disk） RHEL7.x
  - James said that Velocity is in transition to a new machine and will not be able to host at the moment
  - Len said it is OK but need to coordinate access to Vicom Infinity machine
    - Vincent wants to know what packages are needed on the three Linux systems

### Update on how-to access z/VM resource effort
- Vincent needs some requirement for give to his system programmer
  - z/VM version: 7.1
  - Memory: 16 - 24 GB
  - Disk: ???

## Next meeting agenda topics
- Update on CI/CD infrastructure effort
- Update on how-to access z/VM resource effort
- Discussion about core infrastructure badge effort
- Next meeting January 23
  - John will extend call to 45 minutes

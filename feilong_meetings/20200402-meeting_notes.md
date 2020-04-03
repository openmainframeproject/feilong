# 2020/04/02 Feilong project meeting

## Attendees
- Abdullah
- Andrew Grimberg
- Ji Chen
- Daniel Pono Takamori
- James Vincent
- Johan Schelling
- Len Santalucia
- Nick Snel
- Vinnie Terrone
- John Mertic
- Alex Dumitru
- Rudy Grigar
- Trevor Bramwell

## Agenda topics
- Nick Snel with ICU-IT will present his work on the python-zvm-sdk codebase
- Linux Foundation team to discuss the possibility of using Github Actions for driving the CI/CD environment

## Meeting Notes

- View Session recording with audio transcript at https://zoom.us/rec/share/3Z1uKo3gy29LBbfVxRHRVZAMMLn4eaa8h3Me86UEyU_RHjvTokaKmMUJQQalFSyC

### Nick Snel with ICU-IT will present his work on the python-zvm-sdk codebase
- Presentation and demo are recorded at link is above
- The work focuses on finding available LUNs and tracking LUNs that are assigned to guests
- Q&A
  - Q: Can this work automatically to create luns on the storage array?
    - A: No, this was not in the scope of the project but this is something that could be added
  - Q: Are you scanning for any new available luns
    - A: Yes
  - Q: Are you storing lun information in a database
    - A: Yes
  - Q: What is the purpose of the database
    - A: Tracking luns and lun assignments
  - Q: What about security of luns
    - A: Something things have been added to the database but more work needs to be done
- Comments
  - Vinnie is working on an ansible automation to dynamically create luns on ibm storage array
- Nick is willing to join a future Feilong call for additional questions/discussion

### Linux Foundation team to discuss the possibility of using Github Actions for driving the CI/CD environment
- Rudy Grigar lead the presentation
- The slides are available at https://docs.google.com/presentation/d/1FqmTnO5rBzPE9yX0Vh6yznQwGQNzDNAYK9OrXrZQ6CE/edit?usp=sharing
- Presentation is recorded and link is above
- Github Actions could replace Jenkins in the future
- Ji Chen will share presentation with IBM China CI/CD people for review and continued discussion

## Next meeting agenda topics
- Update on CI/CD infrastructure effort
- Update on how-to access second-level VM for developers

### Welcome

We welcome contributions to python-zvm-sdk!


### Repository
The repository for python-zvm-sdk on GitHub:  
https://github.com/mfcloud/python-zvm-sdk

### Reporting bugs
If you are a user and you find a bug, please submit a [bug](https://bugs.launchpad.net/python-zvm-sdk). Please try to provide sufficient information for someone else to reproduce the issue. One of the project's maintainers should respond to your issue within 24 hours. If not, please bump the issue and request that it be reviewed.

### Fixing bugs
Review the [bug list](https://bugs.launchpad.net/python-zvm-sdk) and find something that interests you.

We are using the [GerritHub](https://review.gerrithub.io/) process to manage code contributions.

To work on something, whether a new feature or a bugfix:
  1. Clone python-zvm-sdk locally
  ```
  git clone https://github.com/mfcloud/python-zvm-sdk.git
  ```
  2. Add the GerritHub repository as a remote as gerrit
  ```
  git remote add gerrit ssh://<username>@review.gerrithub.io:29418/mfcloud/python-zvm-sdk
  ```
  Where <username> is your GerritHub username.
  And, you should add the public key of your workstation into your GerritHub SSH public keys.
  3. Create a branch
  Create a descriptively-named branch off of your cloned repository
  ```
  cd python-zvm-sdk
  git checkout -b fix-bug-xxxx
  ```
  4. Commit your code
  Commit to that branch locally
  5. Commit messages
  Commit messages must have a short description no longer than 50 characters followed by a blank line and a longer, more descriptive message that includes reference to issue(s) being addressed so that they will be automatically closed on a merge e.g. ```Closes #1234``` or ```Fixes #1234```.
  6. Run checks
  Run checks via issue:
  ```
  tox -v
  ```
  7. Once all checks passed, you can submit your change for review:
  ```
  git review <branch-name>
  ```
  8. Any code changes that affect documentation should be accompanied by corresponding changes (or additions) to the documentation and tests. This will ensure that if the merged PR is reversed, all traces of the change will be reversed as well.

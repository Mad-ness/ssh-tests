# Test remote clients
The tool log into a remote client by ssh and executes provided shell commands
This is designed for performing automated testing configurations of ssh clients in continues delivery environments

## Contents
The tool includes an executable program written on Python and a set of tests written on declarative manner. YAML syntax is used.

## Program

Main program file is **test_launcher.py**.

To get help run the program with *-h* argument.

```shell
$ python test_launcher.py  -h
usage: test_launcher.py [-h] [-v VARS_FILE] [-e ENV_VAR] -t
                        [TASK_FROM_FILE [TASK_FROM_FILE ...]] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -v VARS_FILE, --vars-file VARS_FILE
                        Load variables from file on a disk
  -e ENV_VAR, --env-var ENV_VAR
                        Passing arguments to a task as var=value. Might be
                        used many times
  -t [TASK_FROM_FILE [TASK_FROM_FILE ...]], --task-from-file [TASK_FROM_FILE [TASK_FROM_FILE ...]]
                        A path to a task in YAML format. Multiple files
                        allowed
  -d, --debug           Debug output
```

The program can load variables from files *--vars-file* option and use variables passed to the command line using *--env-var* variable. Variables passed in a command line has highest priority.

All variables are passed to the task.


## Tests
There is set of predefined tests but you may develop your own.

Each test is a Jinja2 template so any Jinja2 construction also work there. Passing variables to scripts is made using Jinja2.

One test should go per file.

Here is an example of such test.
```yaml
version: v1
metadata:
  title: Checking whether a user {{ username }} dis-/allowed sudo privileges
  description: "Checks whether a user dis-/allowed sudo commands"
  returnCodes:
    pass: {{ rc_pass|default(0) }}
    warn: {{ rc_warn|default(99) }}
  displayStdout: False
  displayStderr: True
  tags: user, sudo
  importance: medium
script: |
  echo '{{ password }}' | sudo -S -l | grep 'not allowed'
  rc=$?
  if [ $rc -eq 1 ]; then
    exit 0
  else
    exit 1
  fi
```
Available options in a test file:
- **version** currently supported value is *v1*
- **metadata** includes meta information about the test
  * **title** a test that is being displayed when running
  * **description** a full description of the test
  * **returnCodes.pass** this return code returned by **shell** code accepted as OK 
  * **returnCodes.warn** this code return also accepted as good
  * **returnCodes.-** there is no **fail** return. All other codes not includes in **pass** and **warn** treated as FAIL
  * **displayStdout** displays the output of the script (not implemented yet, see --debug)
  * **displayStderr** displays errors of the script (not implemented yet, see --debug)
  * **tags** of all passed tests, run only those which has this tag(s)
  * **importance** one of *critical*, *medium*, *none*. Outputs a message with these level (not implemented yet)
- **script** a shell script that is executing on a remote host. Keep the script as simple as possible

Variable **returnCodes.pass** tells which return code of the **script** recognized as successful.


## How to run

### Example 1

Assume we have a file with variables **var.user1.yml** with the content 
```yaml
username: user1
password: Admin123
```
And have a task defined in file **users.ssh_access.yml** with such content:
```yaml
version: v1
metadata:
  title: Checking ssh access of a {{ username }} to a host using password
  description: "It checks whether provided username and password are valid for logging in"
  returnCodes:
    pass: {{ rc_pass | default(0) }}
    warn: 35
  displayStdout: False
  displayStderr: True
  tags: user, ssh, logon
  # importance is any of:
  # - critical - breaks further interrupting
  # - medium - warning but continut is possible
  # - none - any result is acceptable
  importance: critical
script: |
  exit 0
```

The command for running might look like this:
```bash
$ python test_launcher.py  -v vars.user1.yml  -t users.ssh_access.yml  -e host=192.168.3.12
[ OK ] Checking ssh access of a user1 to a host using password
```
We specify username/password in a file and a remote host in a command line


### Example 2
We use the same task and variables but now we tell to the script that expected return code should be 1 to be treated as PASSED.
```bash
$ python test_launcher.py -v vars.user1.yml -t users.ssh_access.yml  -e host=192.168.3.12 -e rc_pass=1
[FAIL] Checking ssh access of a user1 to a host using password
```
Since our script returns 0, the test is recognized as FAILED.

### Example 3
A bunch of tests might be run as this

```bash
$ cat run_tests.sh

#!/bin/bash

###
### Run all tests with proper parameters
###
target_host=192.168.3.14
exe=test_launcher.py

python $exe -t users.ssh_access.yml     -v vars.user1.yml         -e host=$target_host
python $exe -t users.ssh_access.yml     -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t users.ssh_access.yml     -v vars.admin.yml         -e host=$target_host
#
python $exe -t users.take_krbticket.yml -v vars.user1.yml         -e host=$target_host
python $exe -t users.take_krbticket.yml -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t users.take_krbticket.yml -v vars.admin.yml         -e host=$target_host
#
python $exe -t users.sudo_access.yml    -v vars.user1.yml         -e host=$target_host
python $exe -t users.sudo_access.yml    -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t users.sudo_access.yml    -v vars.admin.yml         -e host=$target_host
#
python $exe -t sys.network.yml          -v vars.user1.yml         -e host=$target_host
```
Output is 
```shell
$ sh run_tests.sh
[ OK ] Checking ssh access of a user1 to a host using password
[ OK ] Checking ssh access of a nosudouser1 to a host using password
[ OK ] Checking ssh access of a admin to a host using password
[ OK ] Checking whether a Kerberos ticket might be issued to the user1
[ OK ] Checking whether a Kerberos ticket might be issued to the nosudouser1
[ OK ] Checking whether a Kerberos ticket might be issued to the admin
[ OK ] Checking whether a user user1 dis-/allowed sudo privileges
[ OK ] Checking whether a user nosudouser1 dis-/allowed sudo privileges
[ OK ] Checking whether a user admin dis-/allowed sudo privileges
[ OK ] Checking network settings
```

## Terms of Use
The code is provied AS IS on a free basis. Any improvements are welcome!

## Contacts
Dmitrii Mostovshchikov <dmadm2008@gmail.com>



#!/bin/bash

###
### Run all tests with proper parameters
###
target_host=192.168.3.14
exe=test_launcher.py

python $exe --task users.ssh_access.yml     -v vars.user1.yml         -e host=$target_host

python $exe --task users.ssh_access.yml     -v vars.nosudouser1.yml   -e host=$target_host
python $exe --task users.ssh_access.yml     -v vars.admin.yml         -e host=$target_host
#
python $exe --task users.take_krbticket.yml -v vars.user1.yml         -e host=$target_host
python $exe --task users.take_krbticket.yml -v vars.nosudouser1.yml   -e host=$target_host
python $exe --task users.take_krbticket.yml -v vars.admin.yml         -e host=$target_host
#
python $exe --task users.sudo_access.yml    -v vars.user1.yml         -e host=$target_host
python $exe --task users.sudo_access.yml    -v vars.nosudouser1.yml   -e host=$target_host -e rc_pass=1
python $exe --task users.sudo_access.yml    -v vars.admin.yml         -e host=$target_host -e rc_pass=1
#
python $exe --task sys.network.yml          -v vars.user1.yml         -e host=$target_host
python $exe --task sys.internet.yml         -v vars.user1.yml         -e host=$target_host
python $exe --task sys.internet.yml         -v vars.nosudouser1.yml   -e host=$target_host
python $exe --task sys.internet.yml         -v vars.admin.yml         -e host=$target_host


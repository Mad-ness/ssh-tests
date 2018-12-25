#!/bin/bash

###
### Run all tests with proper parameters
###
target_host=192.168.3.14
exe=test_launcher.py

python $exe -t users.ssh_access.yml     -v vars.user1.yml         -e host=$target_host

exit 0
python $exe -t users.ssh_access.yml     -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t users.ssh_access.yml     -v vars.admin.yml         -e host=$target_host
#
python $exe -t users.take_krbticket.yml -v vars.user1.yml         -e host=$target_host
python $exe -t users.take_krbticket.yml -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t users.take_krbticket.yml -v vars.admin.yml         -e host=$target_host
#
python $exe -t users.sudo_access.yml    -v vars.user1.yml         -e host=$target_host
python $exe -t users.sudo_access.yml    -v vars.nosudouser1.yml   -e host=$target_host -e rc_pass=1
python $exe -t users.sudo_access.yml    -v vars.admin.yml         -e host=$target_host -e rc_pass=1
#
python $exe -t sys.network.yml          -v vars.user1.yml         -e host=$target_host
python $exe -t sys.internet.yml         -v vars.user1.yml         -e host=$target_host
python $exe -t sys.internet.yml         -v vars.nosudouser1.yml   -e host=$target_host
python $exe -t sys.internet.yml         -v vars.admin.yml         -e host=$target_host


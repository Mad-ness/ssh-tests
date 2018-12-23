#!/bin/bash

###
### Run all tests with proper parameters
###
target_host=192.168.3.14
exe=test_launcher.py

for target_host in 192.168.3.13 192.168.3.14; do

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
done


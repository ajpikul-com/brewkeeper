```
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hciconfig`
sudo setcap 'cap_net_raw,cap_net_admin+eip' /home/ajp/envs/brewkeeper/lib/python3.9/site-packages/bluepy/bluepy-helper
```

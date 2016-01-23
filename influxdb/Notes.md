# Todo

add the vlans to main switch ports file 

-----------------

snmpwalk -c public 10.1.4.239

-----------

influx -host 10.1.3.254 

use snmpjunk3

show series

select  column,host,value from ifHCInOctets  where column = 'vlan-blue' 

select last(value)  from ifHCInOctets WHERE column = 'FWInternet' limit 10

-------

graphana


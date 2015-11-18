
notes on compileing influxdb at https://anomaly.io/compile-influxdb/

copy executable to /usr/bin

create the directory for data and make sure it owned by _postgres

create the log files and make sure owned by _postgres

create the DB with something like
echo "create junkdb" | influx -host fs2.iii.ca

test with something like

curl -X POST 'http://fs2.iii.ca:8086/write?db=junkdb' --data-binary 'test/voltage,u=V voltage=122'

curl -G 'http://fs2.iii.ca:8086/query?pretty=true'  --data-urlencode "db=junkdb" \
    --data-urlencode 'q=SELECT * FROM  "test/voltage" '



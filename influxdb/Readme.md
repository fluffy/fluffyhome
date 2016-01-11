
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



CREATE CONTINUOUS QUERY total_energy_min ON fh2 BEGIN SELECT max(v) AS "v" INTO
"fh2"."default".total_energy_min FROM "fh2"."default".senml WHERE n =
'ECM1240-42340-ch1' AND time > now() - 1h AND time < now() GROUP BY time(1m) END

CREATE CONTINUOUS QUERY total_energy_hour ON fh2 BEGIN SELECT max(v) AS "v" INTO
"fh2"."default".total_energy_hour FROM "fh2"."default".senml WHERE n =
'ECM1240-42340-ch1' AND time > now() - 2d AND time < now() GROUP BY time(1h) END

CREATE CONTINUOUS QUERY total_energy_day ON fh2 BEGIN SELECT max(v) AS "v" INTO
"fh2"."default".total_energy_day FROM "fh2"."default".senml WHERE n =
'ECM1240-42340-ch1' AND time > now() - 2d AND time < now() GROUP BY time(1d) END

following does not work

CREATE CONTINUOUS QUERY power_5min_test1 ON fh2 BEGIN SELECT
non_negative_derivative(max(v), 5m) / 300.000 AS "power" INTO
"fh2"."default".power_5min_test1 FROM "fh2"."default".total_energy_min WHERE
time > now() - 30m GROUP BY time(5m) END

select v  from senml where n = 'ECM1240-42340-ch1'

select derivative(v) from senml where n = 'ECM1240-42340-ch1'



SELECT non_negative_derivative(max(v), 5m) / 300.0 AS "power" INTO "fh2"."default".power_5min_test1 FROM "fh2"."default".total_energy_min WHERE time > now() - 30m GROUP BY time(5m)
name: total_energy_min


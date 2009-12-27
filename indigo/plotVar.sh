#!/bin/csh

sqlite3 -list -separator ' ' /Library/Application\ Support/Perceptive\ Automation/Indigo\ 4/IndigoSqlClient/sqlite_db ' SELECT strftime("%s",ts ) AS "time" ,var_value FROM "variable_history" WHERE var_name="temp" ORDER BY ts DESC LIMIT 700 ; ' | awk ' BEGIN { y=""; x=""; first=1;} { if (first) y=$2; else y = y "," $2; if (first) x=$1; else x = x "," $1 ; first=0 } END { print "<img src=\"http://chart.apis.google.com/chart?chxt=x,y&chxr=0|1,70,75&cht=lxy&chtt=temp&chds=1253408130,1253346030,70,75&chs=500x200&chd=t:" x "|" y   "\" />" ; } '




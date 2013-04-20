#/bin/csh 

if ($#argv != 2) then
    echo "Usage: $0 <username> <password>"
    exit -1 
endif

set user=$1
set pwd=$2
set years = 2013

switch ( $user )
  case fluffy:
    set sensors="alarm MAC0060350F3001-SHT-temp ECM1240-42340-ch1 000801ac231E-Temp 7159ee0c9de5-flushMain 7159ee0c9de5-heatA 7159ee0c9de5-heatB 7159ee0c9de5-mainHumidity 7159ee0c9de5-mainTemp 7159ee0c9de5-topHumidity 7159ee0c9de5-topTemp ECM1240-42340-aux1 ECM1240-42340-aux2 ECM1240-42340-aux3 ECM1240-42340-aux4 ECM1240-42340-aux5 ECM1240-42340-ch1 ECM1240-42340-ch2 ECM1240-42340-voltage ECM1240-42414-aux1 ECM1240-42414-aux2 ECM1240-42414-aux3 ECM1240-42414-aux4 ECM1240-42414-aux5 ECM1240-42414-ch1 ECM1240-42414-ch2 ECM1240-42414-voltage Insteon11BA19-flush1 MAC0060350F2812-pres MAC0060350F2812-volume MAC0060350F3001-BMP-pres MAC0060350F3001-BMP-temp MAC0060350F3001-SHT-hum  OneWire000801D2F1E4 OneWire000801EF221E TED5000-00-25-2F-20-08-E0-MTU1 TED5000-00-25-2F-20-08-E0-MTU2 ZB-0013A2004052 ZB-0013A2004052-ch1 arduinoTempA heaterA heaterB mainHumidity mainTemp topFloorHumidity topFloorTemp voltsError"
    breaksw
  case theshire:
    set sensors="ECM1240-5707-ch1 ECM1240-5707-ch2"
    breaksw
  case pgladstone:
    set sensors="ECM1240-5745-aux2 ECM1240-5745-ch1 ECM1240-5745-aux5 ECM1240-5745-aux1 ECM1240-5745-voltage ECM1240-5745-aux3 ECM1240-5745-aux4 ECM1240-5745-ch2 ECM1240-5775-ch2 ECM1240-5723-ch1 ECM1240-5748-aux1 ECM1240-5723-aux1 ECM1240-5748-ch2 ECM1240-5723-ch2 ECM1240-5775-aux1 ECM1240-5723-aux3 ECM1240-5723-aux2 ECM1240-5723-aux4 ECM1240-5723-aux5 ECM1240-5775-aux3 ECM1240-5748-ch1 ECM1240-5748-aux2 ECM1240-5775-aux4 ECM1240-5775-ch1 ECM1240-5748-aux3 ECM1240-5748-aux4 ECM1240-5748-aux5 ECM1240-5775-aux2 ECM1240-5775-aux5"
    breaksw
  case anm:
    set sensors="MAC0060350F2910-ch0"
    breaksw
  case wind:
    set sensors="alberta-1-10-temp alberta-1-10-wind alberta-red-deer-temp alberta-monarch-temp alberta-chestermere-speed alberta-red-deer-speed alberta-canmore-speed alberta-gleichen-speed alberta-chestermere-temp alberta-canmore-temp alberta-monarch-speed alberta-gleichen-temp alberta-gleichen-time alberta-1-14-speed alberta-ab-52-time alberta-ab-29-time alberta-highasakite-speed alberta-red-deer-time alberta-ab-29-temp alberta-ab-29-speed alberta-ab-30-temp alberta-ab-30-speed alberta-3-08b-temp alberta-ab-30-time alberta-2-08-time alberta-chestermere-time alberta-2-08-temp alberta-1-14-temp alberta-1-02-speed alberta-highasakite-temp alberta-3-08b-speed alberta-1-02-time alberta-1-10-speed alberta-highasakite-time alberta-canmore-time alberta-2-08-speed alberta-3-08b-time alberta-1-14-time alberta-ab-52-temp alberta-monarch-time alberta-ab-52-speed alberta-1-10-time alberta-1-02-temp"
    breaksw
endsw

# users are fluffy theshire pgladstone anm wind
setenv user fluffy
foreach year ( $years )

set maxDay = 365
set maxDay = 366
if ( $year == 2013 ) then
    set maxDay = ` date "+%j" | awk '{print $1 + 0}' `
    @ maxDay = $maxDay - 2
endif

set n = 1
while ( $n <= $maxDay )

set day = `printf %03d $n`

foreach sensor ( $sensors )

if( ! -e  dump_${user}_${sensor}_${year}_${day}.xml ) then

echo Fetching $sensor $year $day
curl --digest --user "${user}:${pwd}" http://www.fluffyhome.com/sensor/$user/$sensor/dump/$year/$day/ > tmp$$
mv tmp$$ dump_${user}_${sensor}_${year}_${day}.xml

endif

end # loop on sensor

@ n = $n + 1

end # loop on day 
end #loop on year 


# find . -name "dump*.xml" -type f -exec grep html {} \; -ls | grep dump
# find . -name "dump*.xml" -type f -exec grep html {} \; -exec rm {} \;
# find . -size 0c -exec rm {} \;


all: computePower


computePower: computePower.go 
	go build computePower.go

install: install-computePower install-influxsnmp

install-computePower: 
	- sudo launchctl unload /Library/LaunchDaemons/com.fluffyhome.computepower.plist
	go get github.com/influxdb/influxdb/client/v2
	go install github.com/influxdb/influxdb/client/v2
	go build computePower.go
	sudo cp computePower /usr/local/bin/computePower
	sudo cp com.fluffyhome.computepower.plist /Library/LaunchDaemons/com.fluffyhome.computepower.plist
	sudo launchctl load /Library/LaunchDaemons/com.fluffyhome.computepower.plist


install-influxsnmp:
	- sudo launchctl unload /Library/LaunchDaemons/com.fluffyhome.influxsnmp.plist
	go get github.com/paulstuart/influxsnmp
	go install github.com/paulstuart/influxsnmp
	sudo cp $GOPATH/bin/influxsnmp /usr/local/bin/influxsnmp
	sudo cp com.fluffyhome.influxsnmp.plist /Library/LaunchDaemons/com.fluffyhome.influxsnmp.plist
	- sudo mkdir /var/log/influxsnmp
	- sudo mkdir /etc/influxsnmp
	- sudo mkdir /var/log/influxsnmp
	sudo cp $GOPATH/src/github.com/paulstuart/influxsnmp/oids.txt /etc/influxsnmp/oids.txt
	sudo cp influxsnmp.cfg /etc/influxsnmp/.
	sudo cp deskSwitch.ports /etc/influxsnmp/.
	sudo cp mainSwitch.ports /etc/influxsnmp/.
	sudo launchctl load /Library/LaunchDaemons/com.fluffyhome.influxsnmp.plist


all: computePower


computePower: computePower.go 
	go build computePower.go


install: 
	- sudo launchctl unload /Library/LaunchDaemons/com.fluffyhome.computepower.plist
	go get github.com/influxdb/influxdb/client/v2
	go install github.com/influxdb/influxdb/client/v2
	go build computePower.go
	sudo cp computePower /usr/local/bin/computePower
	sudo cp com.fluffyhome.computepower.plist /Library/LaunchDaemons/com.fluffyhome.computepower.plist
	sudo launchctl load /Library/LaunchDaemons/com.fluffyhome.computepower.plist

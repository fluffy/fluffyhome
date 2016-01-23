
all: 

install:
	- sudo launchctl unload /Library/LaunchDaemons/com.fluffyhome.grafana.plist
	sudo cp $GOPATH/bin/grafana /usr/local/bin/grafana
	sudo cp com.fluffyhome.grafana.plist /Library/LaunchDaemons/com.fluffyhome.grafana.plist
	- sudo mkdir /var/log/grafana
	- sudo mkdir /var/grafana
	sudo launchctl load /Library/LaunchDaemons/com.fluffyhome.grafana.plist

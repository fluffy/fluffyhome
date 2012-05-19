
all: xbee-server

clean:
	- rm xbee-server 

install: xbee-server
	cp xbee-server /usr/bin/xbee-server
	cp com.fluffyhome.xbee.plist /Library/LaunchDaemons/com.fluffyhome.xbee.plist


xbee-server:  xbee-server.c
	cc -o  xbee-server  xbee-server.c -lcurl 


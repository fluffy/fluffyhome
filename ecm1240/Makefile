
all: ecm-server

clean:
	- rm ecm-server 

install: ecm-server
	cp ecm-server /usr/bin/ecm-server
	cp com.fluffyhome.ecm1240.plist /Library/LaunchDaemons/com.fluffyhome.ecm1240.plist


ecm-server:  ecm-server.c
	cc -o  ecm-server  ecm-server.c -lcurl 


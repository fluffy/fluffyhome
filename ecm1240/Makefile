
all: ecm-server

clean:
	- rm ecm-server 

install-mac: ecm-server
	- launchctl unload /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist 
	cp ecm-server /usr/bin/ecm-server
	cp com.fluffyhome.ecm1240-1.plist /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist
	launchctl load /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist 

install-fluffy:
	- launchctl unload /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist 
	- launchctl unload /Library/LaunchDaemons/com.fluffyhome.ecm1240-2.plist 
	cp ecm-server /usr/bin/ecm-server
	cp com.fluffyhome.ecm1240-1.plist /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist
	cp com.fluffyhome.ecm1240-2.plist /Library/LaunchDaemons/com.fluffyhome.ecm1240-2.plist
	launchctl load /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist 
	launchctl load /Library/LaunchDaemons/com.fluffyhome.ecm1240-2.plist 


ecm-server:  ecm-server.c
	cc -o  ecm-server  ecm-server.c -lcurl 

release-src:
	zip ecm1240-src-v0.1.zip *.c *.h *.plist Makefile Readme.txt 

release-osx: ecm-server
	zip ecm1240-osx-v0.1.zip ecm-server *.plist Makefile Readme.txt 



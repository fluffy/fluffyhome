
all: ecm-server

clean:
	- rm ecm-server 

install-mac: ecm-server
	cp ecm-server /usr/bin/ecm-server
	cp com.fluffyhome.ecm1240-1.plist /Library/LaunchDaemons/com.fluffyhome.ecm1240-1.plist


ecm-server:  ecm-server.c
	cc -o  ecm-server  ecm-server.c -lcurl 

release-src:
	zip ecm1240-src-v0.1.zip *.c *.h *.plist Makefile Readme.txt 

release-osx: ecm-server
	zip ecm1240-osx-v0.1.zip ecm-server *.plist Makefile Readme.txt 



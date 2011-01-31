#include <Ethernet.h>

#include "WProgram.h"
void setup();
void loop();
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
byte ip[] = { 10, 0, 1, 66 };
byte server[] = { 74, 125, 95,  147 }; // Google
//byte server[] = { 10, 0, 1, 102 }; 


Client client(server, 80);

void setup()
{
  Ethernet.begin(mac, ip);
  Serial.begin(9600);
  
  delay(1000);
  
  Serial.println("connecting...");
  
  if (client.connect()) {
    Serial.println("connected");
    client.println("GET /search?q=arduino HTTP/1.0");
    client.println();
  } else {
    Serial.println("connection failed");
  }
}

void loop()
{
  if (client.available()) {
    char c = client.read();
    Serial.print(c);
  }
  
  if (!client.connected()) {
    Serial.println();
    Serial.println("disconnecting.");
    client.stop();
    for(;;)
      ;
  }
}

int main(void)
{
	init();

	setup();
    
	for (;;)
		loop();
        
	return 0;
}



#include <Ethernet.h>
#include <EthernetDHCP.h>


byte macAddr[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0x66, 0xED };

byte ip[] = { 
  192, 168,0,66 };

int rLed = 7;
int gLed = 6;

void setup()
{

  pinMode( rLed, OUTPUT );
  pinMode( gLed, OUTPUT );

  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, HIGH );  

  Ethernet.begin(macAddr, ip);

  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, LOW );  

  EthernetDHCP.begin(macAddr);

  digitalWrite( rLed, LOW );  
  digitalWrite( gLed, HIGH );  
}

void loop()
{
}


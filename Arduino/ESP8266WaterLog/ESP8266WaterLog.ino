#include <ESP8266WiFi.h>
#include <EEPROM.h>


char ssid[32];
char password[32];

const char* host = "10.1.3.17";
const int port = 8880;

byte mac[6];

const int sensorPin0 = 4;   // water meter input used for interupt zero
const int sensorPin1 = 13;   // water meter input used for interupt one


void writeEEProm()
{
#if  0
  EEPROM.begin(64);

  byte l = 0;
  char s[] = "FluffyFar2G";
  char c;

  c = 1;
  while (c) {
    c = s[l];
    EEPROM.write(l, c);
    l++;
    if ( l >= 31 ) break;
  }
  EEPROM.write(l, 0);

  l = 0;
  char s2[] = "TODO";

  c = 1;
  while (c) {
    c = s2[l];
    EEPROM.write(32 + l, c);

    l++;
    if ( l >= 31 ) break;
  }
  EEPROM.write(32 + l, 0);

  EEPROM.commit();
#endif
}


void readEEProm()
{
  EEPROM.begin(64);
  byte l = 0;
  byte c;

  l = 0;
  do {
    c = EEPROM.read(l);
    ssid[l++] = c;
  } while ( c );
  ssid[l] = 0;

  l = 0;
  do {
    c = EEPROM.read(32 + l);
    password[l++] = c;
  } while ( c );
  password[l] = 0;
}


volatile int junk = 0;


void ICACHE_RAM_ATTR sensorIsr0()
{
  noInterrupts();
  junk++;
  interrupts();
}


void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println("starting");

#if 1
  writeEEProm();
  readEEProm();

  Serial.print("WIFI SSID=");
  Serial.println( ssid );
  WiFi.begin( ssid, password );

  WiFi.softAPdisconnect( true );

  Serial.print("Connecting to WiFi ");
  while ( WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println();
  Serial.println("connected");
  Serial.print("IP address: ");
  Serial.println( WiFi.localIP() );

  WiFi.macAddress(mac);
  Serial.print("MAC: ");
  for ( byte i = 0; i < 6; i++) {
    if ( mac[i] < 16) Serial.print("0");
    Serial.print( mac[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
#endif

  delay( 1000 );


  pinMode(sensorPin0, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(sensorPin0), sensorIsr0, FALLING);
}




void loop() {
  Serial.println( junk );
  delay( 1000 );

}

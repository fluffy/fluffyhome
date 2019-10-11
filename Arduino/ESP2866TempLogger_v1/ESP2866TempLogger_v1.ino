#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

char ssid[32];
char password[32];

const char* host = "10.1.3.17";
const int port = 8880;

const byte ONE_WIRE_PIN = 0;

OneWire  bus( ONE_WIRE_PIN );
DallasTemperature sensors(&bus);

#define MAX_DEVICES 5
DeviceAddress devAddr[MAX_DEVICES];
byte numDevices = 0;

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


void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println("starting");

  writeEEProm();
  readEEProm();

  // scan 1-wire bus
  Serial.println("Scanning 1-wire bus");
  sensors.begin();
  numDevices = sensors.getDeviceCount();
  Serial.print("Num devices= ");
  Serial.print( numDevices , DEC);
  Serial.println(" devices.");

  if ( numDevices > MAX_DEVICES ) {
    numDevices = MAX_DEVICES;
  }

  delay(250);
  for ( int i = 0; i < numDevices; i++  ) {
    if ( sensors.getAddress( devAddr[i], i ) ) {
      Serial.print("device at =");
      for ( byte j = 0; j < 8; j++) {
        if ( devAddr[i][j] < 16) Serial.print("0");
        Serial.print( devAddr[i][j], HEX);
        Serial.print(" ");
      }
      Serial.println();
      sensors.setResolution(devAddr[i], 12 );
    }
    else {
      Serial.print("could not find device at index ");
      Serial.println(i);
    }
  }


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

  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC =");
  for ( byte i = 0; i < 6; i++) {
    if ( mac[i] < 16) Serial.print("0");
    Serial.print( mac[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  delay( 2000 );
}


void loop() {

  // TODO - should reserver buffer pace for body and hdr strings 
  
  String body;

  body += "[";

  // body += "{ \"n\":\"test\", \"v\":42.1, \"u\":\"Cel\"  }";
  sensors.requestTemperatures();
  for ( int i = 0; i < numDevices; i++  ) {
    delay(100);
    float tempC = sensors.getTempC( devAddr[i] );
    Serial.print("Device ");
    Serial.print( i);
    Serial.print( " has temp ");
    Serial.println( tempC );

    if ( i > 0 ) {
      body += ",";
    }
    body += String("{") + "\"n\":\"urn:dev:ow:";
    for ( byte j = 0; j < 8; j++) {
      if ( devAddr[i][j] < 16) body += "0";
      body += String( devAddr[i][j], HEX );
    }
    body += String("\",\"v\":") + tempC + ",\"u\":\"Cel\"}";
  }

  body += "]\r\n";

  Serial.print("connecting to ");
  Serial.print(host);
  Serial.print(":");
  Serial.print(port);
  Serial.print(" ... ");
  WiFiClient client;
  if (!client.connect( host, port )) {
    Serial.println("connection failed");
    delay( 10000 );
    return;
  }
  Serial.println();


  String hdr;
  hdr += "POST / HTTP/1.1\r\n";
  hdr += String("Host: ") + host + "\r\n";
  hdr += "Connection: close\r\n";
  hdr += String("Content-Length: ") + body.length() + "\r\n";
  hdr += "Content-Type: application/senml+json\r\n";
  client.print( hdr + "\r\n" + body );

  Serial.println("SENT HTTP");
  Serial.println( hdr + "\r\n" + body );

  unsigned long txStart = millis();
  while ( client.connected() ) {
    if ( client.available()) {
      String line = client.readStringUntil('\r');
      Serial.print(line);
    }
    yield();
    unsigned long now = millis();
    if ( now > txStart + 15000 ) {
      Serial.println("HTTP transaction timeed out");
      break ; // timeout transaction after 15 seconds
    }
  }

  Serial.println();
  Serial.println("closing connection");
  client.stop();

  delay( 15000 );
}

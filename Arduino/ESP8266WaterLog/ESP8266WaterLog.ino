//  Copyright 2019, Cullen Jennings

#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include <String.h>
#include <Wire.h>

const char* version = "Fluffy ESP2866 Water Log ver 1.03";

const char* host = "10.1.3.17";
const int port = 8880;

const float m3PerPulse[2] = {
  0.000000724637 * 0.7 , 0.000000724637 * 0.7 
};
// 0.000000724637 m^3 per tick ( 0.72 mL / tick) seems to read about 30 % high
// added a 0.7 correction factor after calibration Oct 19, 20119 

const unsigned char i2cAddr = 0x42; // i2c address for counter chip

const unsigned long maxSendTime   =  60 * 1000; // max time bewteen sends in ms
const unsigned long minSendTime   =  10 * 1000; // min time bewteen sends in ms

volatile unsigned long count[2];     // counter
volatile unsigned long prevTime[2]; // time counter was last sent
volatile unsigned long prevCount[2]; // value of counter when last sent

byte mac[6];

char ssid[32];
char password[32];


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
  Wire.begin();

  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println(version);

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
    if ( mac[i] < 16) Serial.print("0"); // add leading 0 if needed
    Serial.print( mac[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
#endif

  delay( 1000 );

  count[0] = 0;
  prevCount[0] = 0;
  count[1] = 0;
  prevCount[1] = 0;

  unsigned long now;
  now = millis();
  prevTime[0] = now;
  prevTime[1] = now;
}


unsigned long getCount( int ch )
{
  unsigned long data = 0;
  unsigned char* ptr = (unsigned char*)&data;

  Wire.beginTransmission(0x42); // send to dev at addr 42
  Wire.write(ch);
  Wire.endTransmission();

  const unsigned char len = 5; // get 4 bytes + 1 checksum byte 
  Wire.requestFrom( i2cAddr, len);  
  for ( int i = 0;  i < 4; i++ ) {
    //Serial.print( "i=" );  Serial.println( i );
    if (Wire.available() ) {
      *ptr++ =  Wire.read();
      //Serial.println( *(ptr-1) );
    }
    else
    {
      return 0;
    }
  }
  if (Wire.available() ) {
    byte checkSumRecv =  Wire.read();
    byte checkSum = 0x42;
    checkSum ^= data;
    checkSum ^= data >> 8;
    checkSum ^= data >> 16;
    checkSum ^= data >> 24;

    if ( checkSumRecv != checkSum )
    {
      return 0;
    }
  }
  else
  {
    return 0;
  }

  return data;
}


void loop()
{
  for ( int ch = 0; ch <= 1; ch++ ) {
    unsigned long data = getCount( ch );
    if ( data != 0 ) // 0 indicates error on i2c read
    {
      count[ch] = data;
    }
#if 1
    Serial.print( "ch" ); Serial.print( ch) ; Serial.print("="); Serial.println( data );
#endif
  }

  delay(500);
  checkDataToSend(0);

  delay(500);
  checkDataToSend(1);
}


void checkDataToSend(int ch)
{
  static byte flash = 0;

  unsigned long now;

  now = millis();
  //digitalWrite(flashPin, ( (flash++)%2) ? HIGH : LOW);

  if ( (count[ch] != prevCount[ch]) || ( now > prevTime[ch] + maxSendTime ) )
  {
    if ( now > prevTime[ch] + minSendTime )
    {
      sendData( count[ch], now - prevTime[ch], count[ch] - prevCount[ch], ch );
      prevTime[ch] = now;
      prevCount[ch] = count[ch];
    }
  }
}


void sendData( unsigned long count,  unsigned long deltaTime,  unsigned long deltaCount , int ch )
{
  String data;
  data.reserve( 100 );

  float volume = float(count) * m3PerPulse[ch]; //convert to cube meters

  float flow = 0.0;
  if ( ( deltaTime > 1000 ) && (deltaTime < 600000 ) )
  {
    float dt = float(deltaTime) / 1000.0 ; // convert to seconds
    flow = float(deltaCount) * m3PerPulse[ch] / dt;
  }

  // SENML format in rfc8428
  // URN defined in draft-ietf-core-dev-urn
  data = "[{\"n\":\"urn:dev:mac:";

  for ( byte i = 0; i < 6; i++)
  {
    if ( mac[i] < 16) data += '0'; // add leading 0 if needed
    data += String( mac[i], HEX);
  }

  data += "_flow";
  data += ch;

  data += "\",\"v\":";
  data += String( flow , 7 ) ;
  data += ",\"s\":";
  data += String( volume , 7 );
  data += ",\"u\":\"m3/s\"}]";

  Serial.print("SEND to ");
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
  //Serial.println();

  String hdr;
  hdr += "POST / HTTP/1.1\r\n";
  hdr += String("Host: ") + host + "\r\n";
  hdr += "Connection: close\r\n";
  hdr += String("Content-Length: ") + data.length() + "\r\n";
  hdr += "Content-Type: application/senml+json\r\n";
  client.print( hdr + "\r\n" + data );

  //Serial.println("SENT HTTP");
  //Serial.print( hdr + "\r\n"  );
  Serial.print( data );

  Serial.print( " --> " );
  unsigned long txStart = millis();
  bool firstLine = true;
  while ( client.connected() ) {
    if ( client.available()) {
      String line = client.readStringUntil('\r');
      if ( firstLine ) {
        Serial.print(line);
        firstLine = false;
      }
    }
    yield();
    unsigned long now = millis();
    if ( now > txStart + 15000 ) {
      Serial.println("HTTP transaction timeed out");
      break ; // timeout transaction after 15 seconds
    }
  }

  Serial.println();
  //Serial.println("closing connection");
  client.stop();
}

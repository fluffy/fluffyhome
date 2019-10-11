#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include <String.h>

const char* version = "Fluffy ESP2866 Water Log ver 0.02";

const char* host = "10.1.3.17";
const int port = 8880;

const unsigned long bounceTime[2] = {
  2, 2
}; // de bounce time for sensor in ms

const float m3PerPulse[2] = {
  0.000000724637, 0.000000724637
};
// 0.000000724637 m^3 per tick ( 0.72 mL / tick) seems to read about 20% high

const int sensorPin0 = 4;   // water meter input used for interupt zero
const int sensorPin1 = 13;   // water meter input used for interupt one

const unsigned long maxSendTime   =  15000; // max time bewteen sends in ms
const unsigned long minSendTime   =   3000; // min time bewteen sends in ms
const unsigned long minEepromTime = 600000; // min time bewteen eeprom write

volatile unsigned long globalCount[2];     // counter
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


void ICACHE_RAM_ATTR sensorInt(const int ch) __attribute__((always_inline));

void ICACHE_RAM_ATTR sensorInt(const int ch)
{
  unsigned long now;

  now = millis();
  if ( now > prevTime[ch] + bounceTime[ch] )
  {
    noInterrupts();
    globalCount[ch]++;
    prevTime[ch] = now;
    interrupts();
  }

  if ( prevTime[ch] > now )
  {
    prevTime[ch] = now;
  }
}

void ICACHE_RAM_ATTR sensorIsr0() __attribute__((always_inline));
void ICACHE_RAM_ATTR sensorIsr1() __attribute__((always_inline));

void ICACHE_RAM_ATTR sensorIsr0()
{
  sensorInt( 0 );
}


void ICACHE_RAM_ATTR sensorIsr1()
{
  sensorInt( 1 );
}


void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println("starting");

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

  delay( 1000 );

  globalCount[0] = 0;
  prevCount[0] = globalCount[0];
  globalCount[1] = 0;
  prevCount[1] = globalCount[1];

  unsigned long now;
  now = millis();
  prevTime[0] = now;
  prevTime[1] = now;


  pinMode(sensorPin0, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(sensorPin0), sensorIsr0, FALLING);

  pinMode(sensorPin1, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(sensorPin1), sensorIsr1, FALLING);
}


void loop() {
  delay(500);

  //Serial.println( globalCount[0] );
  //Serial.println( globalCount[1] );

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

  if ( (globalCount[ch] != prevCount[ch]) || ( now > prevTime[ch] + maxSendTime ) )
  {
    if ( now > prevTime[ch] + minSendTime )
    {

      // TODO LOCK out interupts and copy volatile data

      sendData( globalCount[ch], now - prevTime[ch], globalCount[ch] - prevCount[ch], ch );
      prevTime[ch] = now;

      if (globalCount[ch] != prevCount[ch])
      {
        prevCount[ch] = globalCount[ch];
      }

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
  hdr += String("Content-Length: ") + data.length() + "\r\n";
  hdr += "Content-Type: application/senml+json\r\n";
  client.print( hdr + "\r\n" + data );

  Serial.println("SENT HTTP");
  Serial.println( hdr + "\r\n" + data );

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
}

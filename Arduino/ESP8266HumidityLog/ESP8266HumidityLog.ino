#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include <String.h>
#include <Wire.h>
#include <Adafruit_Sensor.h> // From https://github.com/adafruit/Adafruit_Sensor 
#include <Adafruit_BME680.h> // From https://github.com/adafruit/Adafruit_BME680

const char* version = "Fluffy ESP2866 Humidity Log ver 0.03";

const char* host = "10.1.3.17";
const int port = 8881;

const unsigned char i2cAddr = 0x42; // i2c address for counter chip

const unsigned long sendTime   =  5 * 1000; // max time bewteen sends in ms

byte mac[6];

char ssid[32];
char password[32];

Adafruit_BME680 bme;


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
  Serial.println("version");

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

  if (!bme.begin()) {
    Serial.println(F("Could not find a valid BME680 sensor, check wiring!"));
  }

  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320 /* degree C */ , 150 /* ms */ );
}


void loop()
{
  delay(100);
  checkDataToSend();
}


void sendInfo( float temperature, float humdity, float pressure, float voc )
{
  String data;
  data.reserve( 100 );

#if 0
  // SENML format in rfc8428
  // URN defined in draft-ietf-core-dev-urn
  data = "[{\"bn\":\"urn:dev:mac:";

  for ( byte i = 0; i < 6; i++)
  {
    if ( mac[i] < 16) data += '0'; // add leading 0 if needed
    data += String( mac[i], HEX);
  }
  data += "_\",";

  data += "\"n\":\"";
  data += "temp";
  data += "\",\"v\":";
  data += String( temperature , 7 ) ;
  data += ",\"u\":\"C\"";
#else
 // SENML format in rfc8428
  // URN defined in draft-ietf-core-dev-urn
  data = "[{\"n\":\"urn:dev:mac:";

  for ( byte i = 0; i < 6; i++)
  {
    if ( mac[i] < 16) data += '0'; // add leading 0 if needed
    data += String( mac[i], HEX);
  }
  data += "_temp";
  data += "\",\"v\":";
  data += String( temperature , 7 ) ;
  data += ",\"u\":\"C\"";
#endif

#if 0
  data += "},{";

  data += "\"n\":\"";
  data += "hum";
  data += "\",\"v\":";
  data += String( humdity , 7 ) ;
  data += ",\"u\":\"%RH\"";

  data += "},{";

  data += "\"n\":\"";
  data += "pres";
  data += "\",\"v\":";
  data += String( pressure , 7 ) ;
  data += ",\"u\":\"Pa\"";

  data += "},{";

  data += "\"n\":\"";
  data += "voc";
  data += "\",\"v\":";
  data += String( voc , 7 ) ;
  data += ",\"u\":\"ohm\"";
#endif

  data += "}]";

  Serial.print("SEND to ");
  Serial.print(host);
  Serial.print(": ");
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

  Serial.print( " -- > " );
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


void checkDataToSend()
{
  static unsigned long prevTime = false;
  static bool firstTime = true;

  unsigned long now = millis();

  if ( (now > prevTime + sendTime) || ( firstTime)  )
  {
    prevTime = now;
    firstTime = false;

    unsigned long endTime = bme.beginReading();
    if (endTime == 0) {
      Serial.println(F("Failed to begin reading : ("));
      return;
    }

    while ( millis() <  endTime ) {
      yield();
      delay( 5 );
    }

    if (!bme.endReading()) {
      Serial.println(F("Failed to complete reading : ("));
      return;
    }

    sendInfo(  bme.temperature,  bme.humidity,  bme.pressure,  bme.gas_resistance );

  }
}

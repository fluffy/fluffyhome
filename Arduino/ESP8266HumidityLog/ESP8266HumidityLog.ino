#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include <String.h>
#include <Wire.h>
#include <Adafruit_Sensor.h> // From https://github.com/adafruit/Adafruit_Sensor 
#include <Adafruit_BME680.h> // From https://github.com/adafruit/Adafruit_BME680
#include <Adafruit_CCS811.h> // From https://github.com/adafruit/Adafruit_CCS811 
#include <Adafruit_HTU21DF.h> // From https://github.com/adafruit/Adafruit_HTU21DF_Library

const char* version = "Fluffy ESP2866 Humidity Log ver 1.03";

const char* host = "10.1.3.17";
const int port = 8880;

#define HAVE_CCS811
//#define HAVE_HTU21DF


const unsigned long sendTime   =  60 * 1000; // max time bewteen sends in ms

byte mac[6];

char ssid[32];
char password[32];


Adafruit_BME680 bme;

#ifdef  HAVE_CCS811
bool ccsValid = false;
Adafruit_CCS811 ccs; // I2C addr 0x5A
#endif


#ifdef  HAVE_HTU21DF
Adafruit_HTU21DF htu = Adafruit_HTU21DF();
#endif


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

#if 1
  if (!bme.begin()) {
    Serial.println(F("Failed BME680 sensor"));
  }
  else
  {
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320 /* degree C */ , 150 /* ms */ );

    Serial.println("BME680 sensor ready");
  }

#endif

#ifdef HAVE_CCS811
  for ( byte i2cAddr = 0x5A; i2cAddr <= 0x5B; i2cAddr++ ) {
    if (!ccs.begin( i2cAddr /*i2c addr*/ )) // address is 5A or 5B
    {
      Serial.print("No CCS811 sensor at 0x");  Serial.println( i2cAddr , HEX);
    }
    else
    {
      while ( !ccs.available() ) {
        yield();
        delay(5);
      }

      ccs.setDriveMode( CCS811_DRIVE_MODE_10SEC );
      Serial.print("CCS811 sensor ready at i2c addr 0x"); Serial.println( i2cAddr, HEX);
      ccsValid = true;
      break;
    }
  }
#endif

#ifdef HAVE_HTU21DF
  if (!htu.begin()) {
    Serial.println("Could not find HTU21DF sensor");
  }
  else {
    Serial.println("HTU21DF sensor ready");
  }
#endif

}


void loop()
{
  delay(500);
  checkDataToSend();

#ifdef HAVE_CCS811
  if ( ccsValid ) {
    if (ccs.available()) {
      if (!ccs.readData()) {
        Serial.print("CO2: "); Serial.print(ccs.geteCO2()); Serial.print(" ppm, TVOC: "); Serial.println(ccs.getTVOC());
      }
      else {
        Serial.println("ERROR Reading CSS811");
      }
    }
  }
#endif
}


void sendInfo( float temperature, float humdity, float pressure, float voc ,
               uint16_t eCO2, uint16_t tVOC,
               float temp2, float hum2)
{
  String data;
  data.reserve( 100 );

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
  data += String( temperature , 2 ) ;
  data += ",\"u\":\"C\"";

  data += "},{";

  data += "\"n\":\"";
  data += "hum";
  data += "\",\"v\":";
  data += String( humdity , 2 ) ;
  data += ",\"u\":\"%RH\"";

  data += "},{";

  data += "\"n\":\"";
  data += "pres";
  data += "\",\"v\":";
  data += String( pressure , 3 ) ;
  data += ",\"u\":\"Pa\"";

  if ( voc > 0.0 ) {
    data += "},{";

    data += "\"n\":\"";
    data += "voc";
    data += "\",\"v\":";
    data += String( voc , 3  ) ;
    data += ",\"u\":\"ohm\"";
  }


  if ( (temp2 >= -273.0) ) {
    data += "},{";

    data += "\"n\":\"";
    data += "temp2";
    data += "\",\"v\":";
    data += String( temp2, 2 ) ;
    data += ",\"u\":\"C\"";
  }

  if ( ( hum2 > 0.0) )  {
    data += "},{";

    data += "\"n\":\"";
    data += "hum2";
    data += "\",\"v\":";
    data += String( hum2 , 2 ) ;
    data += ",\"u\":\"%RH\"";
  }


  if ( (eCO2 >= 400) && ( eCO2 <= 64000u ) ) { // range from datasheet is 400 to 8192 - firmware update says 64000
    data += "},{";

    data += "\"n\":\"";
    data += "eCO2";
    data += "\",\"v\":";
    data += String( eCO2 ) ;
    data += ",\"u\":\"ppm\"";
  }

  if ( ( tVOC >= 0 ) && ( tVOC <= 64000u ))  { // range from datasheet is 0 to 1187 - firmware update says 64000
    data += "},{";

    data += "\"n\":\"";
    data += "tVOC";
    data += "\",\"v\":";
    data += String( tVOC  ) ;
    data += ",\"u\":\"ppm\"";
  }


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

    uint16_t eCO2 = 0 ;
    uint16_t tVOC = 0xFFFFu;

    float hum2 = -1.0;
    float temp2 = -500.0;

#ifdef HAVE_CCS811
    if ( ccsValid )
    {
      eCO2 = ccs.geteCO2();
      tVOC = ccs.getTVOC() ;
      ccs.setEnvironmentalData( int( bme.humidity ) /*uint8_t humidity*/,  bme.temperature /* double temperature*/ );
    }
#endif

#ifdef HAVE_HTU21DF
    temp2 = htu.readTemperature();
    hum2 = htu.readHumidity();

    //Serial.print("Temp2: "); Serial.print(temp2); Serial.print(" "); Serial.print("Hum2: "); Serial.println(hum2);
#endif

    sendInfo(  bme.temperature,  bme.humidity,  bme.pressure,  bme.gas_resistance  , eCO2 , tVOC , temp2, hum2  );
  }
}

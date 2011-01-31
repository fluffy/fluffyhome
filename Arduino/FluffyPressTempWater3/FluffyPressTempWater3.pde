//#include <SPI.h>
#include <PString.h>
#include <Ethernet.h>
#include <EthernetDHCP.h>
#include <EthernetDNS.h>
#include <EEPROM.h>
#include <OneWire.h>

// note the serial port is running at 19.2 Kbps for this one 

#define VERSION  "Fluffy Pressure Temp Water Meter ver 0.03"

const byte debug=1;

const int minPostTime =  5000; // (5 seconds) time in ms 
const int maxPostTime = 60000; // (1 min) time in ms 
const unsigned long minEepromTime = 600000; // (10 min)  min time bewteen eeprom write  

byte macAddr[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0x66, 0xE3 };

//const char* serverName = "wwww.fluffyhome.com"; // double CNAME lookup 
const char* serverName = "g.fluffyhome.com"; // direct A record lookup 
byte ipAddrServer[4];

#define CRLF "\r\n"


// Ethernet  uses digitial IO pins 10,11,12, and 13   
// PWM can be on pins 3,5,6,9,10,11
// PWM is flakey on 5,6 due to timer interaction
// interupts can happend on pin 2 and 3
// TWI aka I2C is on anlog pins 4 and 5 
// running one wire but on pin 7,8
// run the weird SHT75 bus on pin 4 and 5 digital

const int rLed = 7;
const int gLed = 6;
const int bLed = 5;

const int presInput = 0 ; // analog input pin for pressure 
const int waterPulseInput = 1; // anolog input pin that gets input puls counts from water meter 

OneWire  busA(8); // using digiital IO on pin 8
typedef byte DeviceAddr[8];


/********** Global Vars ******************/


int presReading; // in 0-1023 for 0 to 5 v 
unsigned long pulseCount; // number of pulse counts
bool pulseReading; // if current pulse coutner input is low or high  
unsigned long prevEepromTime;

/*******************************/

void getMacAddr( OneWire& bus, DeviceAddr& addr );
unsigned int crc16( byte* data, int len );


void storeEEPROM( unsigned long count , int ch )
{
  //Serial.println( "Write to EEPROM" );

  EEPROM.write( 0 + ch*4, (byte)count );
  count = count >> 8;
  EEPROM.write( 1 + ch*4, (byte)count );
  count = count >> 8;
  EEPROM.write( 2 + ch*4, (byte)count );
  count = count >> 8;
  EEPROM.write( 3 + ch*4, (byte)count );   
}


unsigned long loadEEPROM(int ch)
{
  unsigned long count = 0;
  count = count + EEPROM.read( 3 + ch*4);
  count = count << 8;
  count = count + EEPROM.read( 2 + ch*4);
  count = count << 8;
  count = count + EEPROM.read( 1 + ch*4);
  count = count << 8;
  count = count + EEPROM.read( 0 + ch*4);

  return count;
}



void setup()
{
  delay( 200 );

  // pulseCount = 80*20;  storeEEPROM(pulseCount,0);  

  unsigned long now;
  now = millis();

  pulseCount = loadEEPROM(0); 
  prevEepromTime = now;

restart:


  pinMode( rLed, OUTPUT );
  pinMode( gLed, OUTPUT );
  pinMode( bLed, OUTPUT );


  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, HIGH );  
  digitalWrite( bLed, HIGH );  

  Serial.begin(19200);
  delay( 1000 );

  if (debug) Serial.println( VERSION );


  if (debug) Serial.println("Scanning 1-wire Bus A ...");
  DeviceAddr addr;
  busA.reset_search();
  while ( busA.search(addr) )
  {
    if (debug) Serial.print("Found dev type 0x"); 
    if (debug) Serial.println( int( addr[0] ) , HEX );

    if ( OneWire::crc8( addr, 7) != addr[7]) 
    {
      if (debug) Serial.println("BAD CRC in address");
    }
    else
    {
      if ( addr[0] == 0x10) 
      {
        if (debug) Serial.print("Found temp");

      }
      if ( addr[0] == 0x89) 
      {
        if (debug) Serial.print("Found DS2502-E48 MAC address ");
        getMacAddr( busA, addr );
      }
    }
  }

  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, LOW );  
  digitalWrite( bLed, HIGH );   

  if (debug) Serial.println("DHCP getting IP address ..");
  EthernetDHCP.begin(macAddr);

  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, HIGH );  
  digitalWrite( bLed, LOW );  

  // Since we're here, it means that we now have a DHCP lease, so we print
  // out some information.
  const byte* ipAddr = EthernetDHCP.ipAddress();
  const byte* gatewayAddr = EthernetDHCP.gatewayIpAddress();
  const byte* dnsAddr = EthernetDHCP.dnsIpAddress();

  if (debug) Serial.print("IP Address is ");
  if (debug) printIP(ipAddr);

  if (debug) Serial.print(CRLF "Gateway: ");
  if (debug) printIP(gatewayAddr);

  if (debug) Serial.print(CRLF "DNS server: ");
  if (debug) printIP(dnsAddr);

  EthernetDNS.setDNSServer(dnsAddr);

  if (debug) Serial.print(CRLF "Doing DNS lookup of '");
  if (debug) Serial.print(serverName);
  if (debug) Serial.println("'");
  DNSError err = EthernetDNS.resolveHostName(serverName, ipAddrServer);

  if (DNSSuccess == err)
  {
    if (debug) Serial.print("Server IP is: ");
    if (debug) printIP(ipAddrServer);
    if (debug) Serial.print( CRLF );
  } 
  else
  {
    if (DNSTimedOut == err)
    {
      if (debug) Serial.println("DNS Timed out");
    }
    else if (DNSNotFound == err)
    {
      if (debug) Serial.println("DNS Does not exist");
    } 
    else 
    {
      if (debug) Serial.print("DNS Failed with error code ");
      if (debug) Serial.println((int)err, DEC);
    } 

    digitalWrite( rLed, HIGH );  
    digitalWrite( gLed, LOW );  
    digitalWrite( bLed, HIGH );  

    // TODO - what to do? wait few seconds and reset ?
    delay( 15000 );

    digitalWrite( rLed, LOW );  
    digitalWrite( gLed, LOW );  
    digitalWrite( bLed, LOW );

    delay( 500 );
    goto restart;
  }

  digitalWrite( rLed, LOW );  
  digitalWrite( gLed, LOW );  
  digitalWrite( bLed, HIGH );  

}


void sendData()
{
  digitalWrite( bLed, HIGH );  
  digitalWrite( gLed, LOW );  
  digitalWrite( rLed, LOW );  

  float pres = presReading; // 1023 is 100 PSI ; 1psi = 6.8947 kPa 
  pres = pres*673.97; // convert to Pa 

  float vol = pulseCount; // 75.7 pulse per gallon 
  vol = vol * 0.0500; // convert to liters 

  Client tcp( ipAddrServer , 80 /*port */ );

  //Serial.println("connecting...");

  if (tcp.connect()) 
  {
    //Serial.println("connected");

    char bufStore[256];
    PString data(bufStore, sizeof(bufStore));

    data += "{\"m\":[" CRLF ; 

    data += "  {\"n\":\"MAC";
    for( int i = 0; i < 6; i++)
    {
      data.print(macAddr[i]/16, HEX);
      data.print(macAddr[i]%16, HEX);
    }  
    data += "-pres\", \"v\":"; 
    data += pres ; 
    data += " , \"u\":\"Pa\" }," CRLF;

    data += "  {\"n\":\"MAC";
    for( int i = 0; i < 6; i++)
    {
      data.print(macAddr[i]/16, HEX);
      data.print(macAddr[i]%16, HEX);
    }  
    data += "-volume\", \"s\":"; 
    data += vol ; 
    data += " , \"u\":\"l/s\" }" CRLF;

    data +="]}";

    tcp.print( "POST /sensorValues/ HTTP/1.1" CRLF
      "User-Agent: " VERSION  " " CRLF
      "Host: www.fluffyhome.com" CRLF // todo fix 
    "Accept: */" "*" CRLF
      "Content-Type: application/senmn+xml" CRLF
      "Content-Length: " );
    tcp.print( data.length() );
    tcp.print( CRLF CRLF );
    tcp.print( data );

    if (debug) Serial.print( "Data len=" );
    if (debug) Serial.print( data.length() );
    if (debug) Serial.print( " is: " );
    if (debug) Serial.println( data );

    unsigned long reqTime = millis();

    // wait for a response and disconnect 
    int readCount = 0;
    while ( (readCount < 25 ) and ( millis() < reqTime + 10000 )) // wait 10 seconds for response  
    {
      if (tcp.available()) 
      {
        char c = tcp.read(); 
        readCount++;
        if (debug) Serial.print(c);
      }

      if (!tcp.connected()) 
      {
        if (debug) Serial.println();
        if (debug) Serial.println("server disconnected");
        break;
      }
    }

    //Serial.println("tcp disconnecting");
    tcp.stop();
  } 
  else 
  {
    if (debug) Serial.println("TCP connection failed");
    digitalWrite( rLed, HIGH );  
  } 

  digitalWrite( bLed, LOW );  
  digitalWrite( gLed, HIGH );  
}


void filterData()
{
  static unsigned long prevTime=0;
  unsigned long now = millis();
  static int prevPres=0;
  static long prevPulse=0;

  byte doPost =0;

  if ( now - prevTime < minPostTime )
  {
    return;
  }
  if ( now - prevTime > maxPostTime )
  {
    doPost = 1;
  }

  if ( abs( prevPres - presReading ) > 50 /* 5 psi */ )
  {
    doPost = 1;
  }

  if ( abs( prevPulse - pulseCount ) > 10 /* half a liter  */ )
  {
    doPost = 1;
  }

  if ( doPost )
  {
    sendData();
    prevTime = now;
    prevPres = presReading;
    prevPulse = pulseCount;

    if ( now > prevEepromTime + minEepromTime )
    {
      storeEEPROM(pulseCount,0);  
      prevEepromTime = now;
    }
  }
}




void printIP(const byte* ip)
{
  char buf[6];
  if (debug) Serial.print(itoa(ip[0],buf,10));
  if (debug) Serial.print(".");
  if (debug) Serial.print(itoa(ip[1],buf,10));
  if (debug) Serial.print(".");
  if (debug) Serial.print(itoa(ip[2],buf,10));
  if (debug) Serial.print(".");
  if (debug) Serial.print(itoa(ip[3],buf,10));
}


void getMacAddr( OneWire& bus, DeviceAddr& addr )
{
  int i;  
  bus.reset();
  bus.select(addr);

  bus.write(0xF0); // read memory      
  bus.write(0x00); // addr low     
  bus.write(0x00); // addr high      

  int ack = bus.read();

  byte data[13];
  for (  i = 0; i < 13; i++)
  {          
    data[i] = bus.read();
  }

  // comput the CRC-16
  //unsigned int crc = bus.crc16( (unsigned short*)data, 0x0b/2 ); // this does not work 
  unsigned int crc = crc16( data, 0x0B );
  unsigned int icrc = (data[0x0c]<<8) + data[0x0b];
  if ( ~icrc != crc )
  {
    if (debug) Serial.print("BAD CRC - EUI48 data");
  }

  if (debug) Serial.print(" MAC:");
  int j=0;
  for ( i = 10; i > 4; i--)
  {          
    if (debug) Serial.print(data[i]/16, HEX);
    if (debug) Serial.print(data[i]%16, HEX);
    macAddr[j++] = data[i];
  }
  if (debug) Serial.println("");  
}


unsigned int crc16( byte* data, int len )
{
  unsigned int crc = 0;
  int b,i,j;
  for ( b=0; b<len ; b++ )
  {
    char c = data[b];
    for( i=0;i<8; c >>= 1 , i++ )
    {
      j = (c^crc) & 1;
      crc >>= 1;
      if ( j )
      {
        crc ^= 0xA001;
      }
    }
  }
  return crc;
}



void loop()
{
  // get water pressure 
  presReading = analogRead( presInput ); // full range is 1023 = 100 PSI 

  // get pulse counter for water meter 
  int val = analogRead(waterPulseInput); // full range is about 0 to 100 
  if ( val < 25 ) 
  {
    pulseReading = false;
  }
  if ( val > 75 )
  {
    if ( pulseReading == false )
    {
      pulseCount++;       
    }
    pulseReading = true;
  }

  // get temperature 

    filterData( );
}


















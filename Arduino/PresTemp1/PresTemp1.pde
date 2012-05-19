/*
  Copyright (c) 2009, Cullen Jennings
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification,
 are permitted provided that the following conditions are met:
 
 * Redistributions of source code must retain the above copyright notice, this list
 of conditions and the following disclaimer.
 
 * Redistributions in binary form must reproduce the above copyright notice, this
 list of conditions and the following disclaimer in the documentation and/or
 other materials provided with the distribution.
 
 * Neither the name of Cullen Jennings nor the names of its contributors may be
 used to endorse or promote products derived from this software without specific
 prior written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
 ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <PString.h>
#include <Ethernet.h>
#include <EthernetDHCP.h>
#include <EthernetDNS.h>
#include <EEPROM.h>
#include <OneWire.h>

#define CRLF "\r\n"

#define VERSION  "FluffyHome WaterPres Ver 0.01a"

const byte use1wireA = 1;
const byte use1wireB = 1;

const byte debug=1;

// Ethernet  uses digitial IO pins 10,11,12, and 13   
// PWM can be on pins 3,5,6,9,10,11
// PWM is flakey on 5,6 due to timer interaction
// interupts can happend on pin 2 and 3
// TWI aka I2C is on anlog pins 4 and 5 
// running one wire but on pin 7,8
// run the weird SHT75 bus on pin 4 and 5 digital

int rLed = 7;
int gLed = 6;
int bLed = 5;

OneWire  busA(8); // using digiital IO on pin 8
OneWire  busB(7); // using digiital IO on pin 7

const int vSensorPin = 0;    // analog pin for water pressure sensor


byte macAddr[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xE1 };


typedef byte DeviceAddr[8];
DeviceAddr tempA[2]; 
int numTempA=0;
DeviceAddr tempB[2]; 
int numTempB=0;

const char* serverName = "g.fluffyhome.com"; // direct A record lookup 
byte ipAddrServer[4];


void copyAddr( DeviceAddr& src, DeviceAddr& dst )
{
  for( int i=0; i<8; i++ )
  {
    dst[i]=src[i];
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
    Serial.print("BAD CRC - EUI48 data");
  }

  Serial.print(" MAC:");
  int j=0;
  for ( i = 10; i > 4; i--)
  {          
    Serial.print(data[i]/16, HEX);
    Serial.print(data[i]%16, HEX);
    macAddr[j++] = data[i];
  }
  Serial.println("");  
}


void setup(void)
{
  delay( 200 );

restart:


  pinMode( rLed, OUTPUT );
  pinMode( gLed, OUTPUT );
  pinMode( bLed, OUTPUT );


  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, HIGH );  
  digitalWrite( bLed, HIGH );  


  // start serial port
  Serial.begin(9600);

  Serial.println( VERSION );

  if ( use1wireA)
  {
    Serial.println("Scanning 1-wire Bus A ...");
    DeviceAddr addr;
    busA.reset_search();
    while ( busA.search(addr) )
    {
      if ( OneWire::crc8( addr, 7) != addr[7]) 
      {
        Serial.println("BAD CRC in address");
      }
      else
      {
        if ( addr[0] == 0x10) 
        {
          Serial.println("Found DS18S20 Temperature on bus A");
          if ( numTempA < 2 )
          {
            copyAddr( addr, tempA[numTempA++] );
          }
        }
        if ( addr[0] == 0x89) 
        {
          Serial.print("Found DS2502-E48 MAC address ");
          getMacAddr( busA, addr );
        }
      }
    }
  }

  if (use1wireB)
  {
    Serial.println("Scanning 1-wire Bus B ...");
    DeviceAddr addr;
    busB.reset_search();
    while ( busB.search(addr) )
    {
      if ( OneWire::crc8( addr, 7) != addr[7]) 
      {
        Serial.println("BAD CRC in address");
      }
      else
      {
        if ( addr[0] == 0x10) 
        {
          Serial.println("Found DS18S20 Temperature on bus B");
          if ( numTempB < 2 )
          {
            copyAddr( addr, tempB[numTempB++] );
          }
        }
        if ( addr[0] == 0x89) 
        {
          Serial.print("Found DS2502-E48 MAC address ");
          getMacAddr( busA, addr );
        }
      }
    }
  }

  Serial.println("DHCP getting IP address ..");
  EthernetDHCP.begin(macAddr);

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
  Serial.println("Setup complete");

}


void sendData( char* name, float value, char* units )
{
  digitalWrite( bLed, HIGH );  
  digitalWrite( gLed, LOW );  
  digitalWrite( rLed, LOW );  

  Client tcp( ipAddrServer , 80 /*port */ );

  //Serial.println("connecting...");

  if (tcp.connect()) 
  {
    //Serial.println("connected");

    char bufStore[128];
    PString data(bufStore, sizeof(bufStore));

    data += "{\"m\":[{\"n\":\"MAC";
    for( int i = 0; i < 6 ; i++ )
    {
      data.print(macAddr[i]/16, HEX);
      data.print(macAddr[i]%16, HEX);
    }
    data += name;  
    data += "\",\"v\":"; 
    data += value ;
    data += ",\"u\":\"";
    data += units;
    data += "\"}]}";

    tcp.print( "POST /sensorValues/ HTTP/1.1" CRLF
      "User-Agent: " VERSION  " " CRLF
      "Host: www.fluffyhome.com" CRLF // todo fix 
    "Accept: */" "*" CRLF
      "Content-Type: application/senmn+json" CRLF
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
        Serial.print(c);
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



float getTemp( OneWire& bus, DeviceAddr& addr )
{
  bus.reset();
  bus.select(addr);
  bus.write(0x44,1);  // do conversion 

  delay(750);    

  bus.reset();
  bus.select(addr);    
  bus.write(0xBE);  // read results

  byte data[9];
  for ( int i = 0; i < 9; i++) 
  {          
    data[i] = bus.read();
  }
  if ( OneWire::crc8( data, 8) != data[8] )
  {
    Serial.print("BAD CRC in Temperature");
    return 0.0;
  }

  int temp2x = (data[1]<<8) + data[0];
  int temp16x = (temp2x>>1)*16 - 4 + 16 - data[6] ;
  float temp= temp16x/16.0;

  return temp;
}


void loop(void)
{ 
  int i;
  //Serial.println("");

  if (use1wireA )
  {
    for( i=0; i<numTempA; i++) // scan bus A
    {
      float temp = getTemp( busA, tempA[i] );
      //sendData( tempA[i] , temp );
      delay(1000);
    }
  }
  if (use1wireB)
  {
    for( i=0; i<numTempB; i++) // scan bus B
    {
      float temp = getTemp( busB, tempB[i] );
      //sendData( tempB[i] , temp );
      delay(1000);
    }
  }

  if (1)
  {
    int vSen;
    vSen = analogRead(vSensorPin);      
    float v = vSen;
    v = v * 5.0 / 1024.0; // convert to volts 

    v = v - 0.025; // remove offset 
    v = v * 50.0 / 2.531 ; // conver to PSI 

    v = v * 6.894e3 ; // convert to Pa 
    sendData( "-waterPres", v, "Pa" );
  }


  ////////////////////////////////////////////
  //delay(5000);
  
  delay(30000);
  delay(20000);
}




















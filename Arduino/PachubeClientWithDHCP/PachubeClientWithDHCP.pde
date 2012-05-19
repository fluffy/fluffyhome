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

#include <string.h>
#include <Ethernet.h>
#include <Dhcp.h>
#include <OneWire.h>
#include <DallasTemperature.h>

char PACHUBE_API_STRING[] = "db0ed854fb5ab43a95e8cbe08b02c313cb5283e23657c4d5650270754b4b316a";
int PACHUBE_FEED_ID = 4053; 

// Digital IO port used for one wire interface
int ONE_WIRE_BUS = 8 ;

// Ethernet mac address - this needs to be unique
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

// IP addres of www.pachube.com
byte server[] = { 209,40,205,190 }; // Pachube

char version[] = "PachubeClientWithDHCP Ver 0.01c";


#define CRLF "\r\n"

// simple web client to connect to Pachube.com 
Client client(server, 80);

// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);

// 1wire device address
DeviceAddress thermometer;


int dhcpInit()
{
   Serial.println("getting ip address with DHCP...");
   int result = Dhcp.beginWithDHCP(mac);
   
   if(result == 1)
   {
      byte buffer[4];   
   
      Dhcp.getLocalIp(buffer);
      Serial.print("IP address: ");
      printIP(&Serial, buffer );
      Serial.println("");
    
      Dhcp.getSubnetMask(buffer);
      Serial.print("subnet mask: ");
      printIP(&Serial, buffer );
      Serial.println("");
    
      Dhcp.getGatewayIp(buffer);
      Serial.print("gateway : ");
      printIP(&Serial, buffer );
      Serial.println("");
    
      Dhcp.getDnsServerIp(buffer);
      Serial.print("dns server ip: ");
      printIP(&Serial, buffer );
      Serial.println("");
    
      delay(2000);
   }
   else
   {
      Serial.println("DHCP failed");  
   }
  
   Serial.println("");
   return result;
}


void setup()
{
   // Note: Ethernet shield uses digitial IO pins 10,11,12, and 13   
   Serial.begin(9600);
  
   Serial.println(version);
   Serial.println();
  
   // locate devices on the 1Wire bus
   Serial.print("Locating devices on 1Wire bus...");
   sensors.begin();
   int count = sensors.getDeviceCount();
   Serial.print("Found ");
   Serial.print( count );
   Serial.println(" devices on 1wire bus");

   // select the first sensor   
   for ( int i=0; i<count; i++ )
   {
      if ( sensors.getAddress(thermometer, i) ) 
      {
         Serial.print("1wire device ");
         Serial.print(i);
         Serial.print(" has address: ");
         printAddress(thermometer);
         Serial.println();
      }
      else
      {
         Serial.print("Unable to find address for 1wire device "); 
         Serial.println( i );
      }  
   }
  
   // if you want to use a particular sensor, you can hard code it here 
   if (0)
   { 
      DeviceAddress addr = { 0x10, 0xE4, 0xF1, 0xD2, 0x01, 0x08, 0x00, 0xBE };
      for (uint8_t i = 0; i < 8; i++)
      {
         thermometer[i] = addr[i];
      }
   }
  
   // show the addresses we found on the bus
   Serial.print("Using 1wire device: ");
   printAddress(thermometer);
   Serial.println();

   // set the resolution to 9 bit 
   sensors.setResolution(thermometer, 9);
  
   dhcpInit();
}


void printIP(Print *stream, byte* ip)
{
   char buf[6];
   stream->print(itoa(ip[0],buf,10));
   stream->print(".");
   stream->print(itoa(ip[1],buf,10));
   stream->print(".");
   stream->print(itoa(ip[2],buf,10));
   stream->print(".");
   stream->print(itoa(ip[3],buf,10));
}


void sendData()
{     
   //float temp = sensors.getTempC(thermometer);
   float temp = sensors.getTempF(thermometer);
   Serial.print("Temp=");
   Serial.println(temp);
  
   Serial.println("connecting...");

   if (client.connect()) 
   {
      Serial.println("connected");
      
      client.print(
         "PUT /api/feeds/" );
      client.print(PACHUBE_FEED_ID);
      client.print(".csv HTTP/1.1" CRLF
                   "User-Agent: Fluffy Arduino Ver 0.01" CRLF
                   "Host: www.pachube.com" CRLF 
                   "Accept: */" "*" CRLF  // need to fix this 
                   "X-PachubeApiKey: " );
      client.print(PACHUBE_API_STRING);
      client.print( CRLF 
                    "Content-Length: 5" CRLF
                    "Content-Type: application/x-www-form-urlencoded" CRLF
                    CRLF );
      client.println(temp);
      unsigned long reqTime = millis();
      
      // wait for a response and disconnect 
      while ( millis() < reqTime + 10000) // wait 10 seconds for response  
      {
         if (client.available()) 
         {
            char c = client.read();
            Serial.print(c);
         }

         if (!client.connected()) 
         {
            Serial.println();
            Serial.println("server disconnected");
            break;
         }
      }
      
      Serial.println("client disconnecting");
      Serial.println("");
      client.stop();
   } 
   else 
   {
      Serial.println("connection failed");
   }
}


// function to print a device address
void printAddress(DeviceAddress deviceAddress)
{
   for (uint8_t i = 0; i < 8; i++)
   {
      if (deviceAddress[i] < 16) Serial.print("0");
      Serial.print(deviceAddress[i], HEX);
   }
}


void loop()
{
   // keep DHCP refreshed 
   static int count=10;
   while( count <= 0 ) // keep trying DHCP
   {
      if ( dhcpInit() )
      {
         count = 10 ; // refresh DHCP every 50 minutes 
      }
   }
   count--;
   
   sensors.requestTemperatures(); // Send the command to get temperatures
  
   sendData();
   delay( ( 5l * 60l * 1000l) - 11000l  ); // wait 5 minutes
}


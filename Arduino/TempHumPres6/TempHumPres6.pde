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
#include <OneWire.h>
#include <Wire.h>

static char version[] = "FluffyHome TempHumPres Ver 0.02a";

const byte useSHT = 1;
const byte useBMP = 1;
const byte use1wireA = 1;
const byte use1wireB = 1;


// Ethernet  uses digitial IO pins 10,11,12, and 13   
// PWM can be on pins 3,5,6,9,10,11
// PWM is flakey on 5,6 due to timer interaction
// interupts can happend on pin 2 and 3
// TWI aka I2C is on anlog pins 4 and 5 
// running one wire but on pin 7,8
// run the weird SHT75 bus on pin 4 and 5 digital


OneWire  busA(8); // using digiital IO on pin 8
OneWire  busB(7); // using digiital IO on pin 7

int busCdataPin = 4; // bus C is for the SHT75 humidity sensor
int busCClkPin = 5;

byte macAddr[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

typedef byte DeviceAddr[8];
DeviceAddr tempA[2]; 
int numTempA=0;
DeviceAddr tempB[2]; 
int numTempB=0;

const int bmp085Addr = 0x77;


struct   // calibration coef for BMP085 
{
  int ac1;
  int ac2; 
  int ac3; 
  unsigned int ac4;
  unsigned int ac5;
  unsigned int ac6;
  int b1; 
  int b2;
  int mb;
  int mc;
  int md;
} 
coef;


void copyAddr( DeviceAddr& src, DeviceAddr& dst )
{
  for( int i=0; i<8; i++ )
  {
    dst[i]=src[i];
  }
}


void startSHT75()
{
  pinMode(busCClkPin,OUTPUT);
  pinMode(busCdataPin,OUTPUT);
  digitalWrite(busCdataPin,HIGH);
  digitalWrite(busCClkPin,HIGH);
  digitalWrite(busCdataPin,LOW);
  digitalWrite(busCClkPin,LOW);
  digitalWrite(busCClkPin,HIGH);
  digitalWrite(busCdataPin,HIGH);
  digitalWrite(busCClkPin,LOW);
}


void resetSHT75()
{
  pinMode(busCdataPin,OUTPUT);
  pinMode(busCClkPin,OUTPUT);

  shiftOut(busCdataPin, busCClkPin, LSBFIRST, 0xFF);
  shiftOut(busCdataPin, busCClkPin, LSBFIRST, 0xFF);

  digitalWrite(busCdataPin,HIGH);
  for(int i = 0; i < 15; i++)
  {
    digitalWrite(busCClkPin, LOW);
    digitalWrite(busCClkPin, HIGH);
  }
}



void writeByteSHT75(byte data)
{ 
  int i;
  pinMode(busCClkPin,OUTPUT);
  pinMode(busCdataPin,OUTPUT);  
  shiftOut(busCdataPin,busCClkPin,MSBFIRST,data);
  pinMode(busCdataPin,INPUT);
  i=0;
  while(digitalRead(busCdataPin) == 1);
  digitalWrite(busCClkPin,HIGH);
  digitalWrite(busCClkPin,LOW); 
  i = 0;
  while(digitalRead(busCdataPin) == 0 );
  i = 0;
  while(digitalRead(busCdataPin) == 1 )
  {
    i++;
    if (i == 255) break;
    delay(10);
  } 
}


int readWordSHT75()
{
  int cwt = 0;
  unsigned int bitmask = 32768;
  int temp;

  pinMode(busCdataPin,INPUT);
  pinMode(busCClkPin,OUTPUT);

  digitalWrite(busCClkPin,LOW);

  for(int i = 0; i < 17; i++)
  {
    if(i != 8)
    {
      digitalWrite(busCClkPin,HIGH);
      temp = digitalRead(busCdataPin);
      cwt = cwt + bitmask * temp;
      digitalWrite(busCClkPin,LOW);
      bitmask=bitmask/2;
    }
    else
    {
      pinMode(busCdataPin,OUTPUT);
      digitalWrite(busCdataPin,LOW);
      digitalWrite(busCClkPin,HIGH);
      digitalWrite(busCClkPin,LOW);
      pinMode(busCdataPin,INPUT); 
    }
  }
  digitalWrite(busCClkPin,HIGH);
  return cwt;
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
  // start serial port
  Serial.begin(9600);
  Serial.println( version );

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

  if (useSHT)
  {
    // do bus C for SHT75
    pinMode(busCdataPin,OUTPUT);
    pinMode(busCClkPin,OUTPUT);
    Serial.println("Resetting SHT...");
    resetSHT75();
  }

  //////////////////////////////////////////


  if ( useBMP )
  {
    Serial.println("Scanning BMP085 bus ...");

    Wire.begin();

    // load the calbration coefecceints
    Wire.beginTransmission(bmp085Addr);
    Wire.send(0xAA);  // addr of coef 
    Wire.endTransmission();
    Wire.requestFrom(bmp085Addr, sizeof(coef) ); // number of bytes to read 
    byte* p = (byte*)(&coef);
    for( int i=0; i < sizeof(coef)/2 ; i++ )
    {
      while ( !Wire.available() ) 
      {
        // todo add timeout 
      }  
      byte msb = Wire.receive();
      while ( !Wire.available() ) 
      {
        // todo add timeout 
      }  
      byte lsb = Wire.receive();
      *(p++) = lsb;
      *(p++) = msb;
    }

    if (1)
    {
      // print the coef table 
      Serial.println("Calibration Coef for BMP085");
      Serial.print("AC1: ");
      Serial.println( coef.ac1);
      Serial.print("AC2: ");
      Serial.println( coef.ac2);
      Serial.print("AC3: ");
      Serial.println( coef.ac3);
      Serial.print("AC4: ");
      Serial.println( coef.ac4);
      Serial.print("AC5: ");
      Serial.println( coef.ac5);
      Serial.print("AC6: ");
      Serial.println( coef.ac6);
      Serial.print("B1: ");
      Serial.println( coef.b1);
      Serial.print("B2: ");
      Serial.println( coef.b2);
      Serial.print("MB: ");
      Serial.println( coef.mb);
      Serial.print("MC: ");
      Serial.println( coef.mc);
      Serial.print("MD: ");
      Serial.println( coef.md);
    }
  }

  Serial.println("Setup complete");

}


float getTemp( OneWire& bus, DeviceAddr& addr )
{
  bus.reset();
  bus.select(addr);
  bus.write(0x44,1);  // do conversion 

  delay(750);  // 750 ms for conversion time   

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


void sendData( DeviceAddr& addr, float value )
{
  char bufStore[80];
  PString data(bufStore, sizeof(bufStore));

  data += "{\"m\":[{ \"n\":\"OneWire";
  for( int i = 6; i >= 1; i--)
  {
    data.print(addr[i]/16, HEX);
    data.print(addr[i]%16, HEX);
  }  
  data += "\", \"v\": "; 
  data += value ;
  data += " , \"u\":\"C\" }]}";

  Serial.println( data );
}


void sendData( char* name, float value, char* units )
{
  char bufStore[80];
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

  Serial.println( data );
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
      sendData( tempA[i] , temp );
      delay(1000);
    }
  }
  if (use1wireB)
  {
    for( i=0; i<numTempB; i++) // scan bus B
    {
      float temp = getTemp( busB, tempB[i] );
      sendData( tempB[i] , temp );
      delay(1000);
    }
  }

  ////////////////////////////////////////////

  // do the SHT75
  if (useSHT)
  {
    startSHT75();
    writeByteSHT75(B0000011);
    int x= readWordSHT75();
    //Serial.print("Tempature: ");
    //Serial.println(x);
    float t = -39.65 + 0.01 * float( x );
    //Serial.println( t );
    sendData("-SHT-temp",t,"C");
    delay(1000);

    startSHT75(); // is this needed ?
    writeByteSHT75(B00000101);
    x = readWordSHT75();
    //Serial.print("Humidity: ");
    //Serial.println(x);  
    float rh = -2.0468 + 0.0367 * float( x ) - 1.5955e-6 * float(x) * float(x) ;
    float tc = ( t - 25.0 ) * (0.01 + 0.00008 * float(x) );
    rh += tc;
    //Serial.println(rh);  
    sendData("-SHT-hum",rh,"%RH");
    delay(1000);

  }


  ///////////////////////////////////////

  if (useBMP)
  {
    byte msb, lsb, xlsb;
    int oss = 3; // set over sampling 

    // read UT - save 0x2E at 0xF4 then read 0XF6 
    Wire.beginTransmission(bmp085Addr);
    Wire.send(0xF4);
    Wire.send(0x2E);
    Wire.endTransmission();
    delay(5); 
    Wire.beginTransmission(bmp085Addr);
    Wire.send(0xF6);  // register to read
    Wire.endTransmission();
    Wire.requestFrom(bmp085Addr, 2); // num bytes to read
    while(!Wire.available()) 
    {
    }
    msb = Wire.receive();
    while(!Wire.available())
    {
    }
    lsb = Wire.receive();
    int ut = msb;
    ut <<= 8;
    ut += lsb;
    //Serial.print( "ut=");
    //Serial.println( ut );

    // read UP 
    Wire.beginTransmission(bmp085Addr);
    Wire.send(0xF4);
    Wire.send( 0x34 + (oss<<6) );
    Wire.endTransmission();
    switch (oss)
    {
    case 0: 
      delay(5); 
      break;
    case 1: 
      delay(8); 
      break;
    case 2: 
      delay(14); 
      break;
    case 3: 
      delay(26); 
      break;
    }
    Wire.beginTransmission(bmp085Addr);
    Wire.send(0xF6);  // register to read
    Wire.endTransmission();
    Wire.requestFrom(bmp085Addr, 3); // num bytes to read
    while(!Wire.available()) 
    {
    }
    msb = Wire.receive();
    while(!Wire.available())
    {
    }
    lsb = Wire.receive();
    while(!Wire.available())
    {
    }
    xlsb = Wire.receive();

    long up = msb;
    up <<= 8;
    up += lsb;
    up <<= 8;
    up += xlsb;
    up >>= (8-oss);

    //Serial.print( "up=");
    //Serial.println( up );

    // compute temp and pressure 
    long x1, x2, b5, t, b6, x3, b3, p , b1, b2;
    unsigned long  b4, b7;

    x1 = ((long)ut - coef.ac6) * coef.ac5 >> 15;
    x2 = ((long) coef.mc << 11) / (x1 + coef.md);
    b5 = x1 + x2;
    t = (b5 + 8) >> 4;

    //Serial.print( "t=");
    //Serial.print( t/10 );
    //Serial.print( "." );
    //Serial.print( t%10 );
    //Serial.println( " C" );

    float ft = t;
    ft = ft / 10.0;
    sendData("-BMP-temp",ft,"C");
    delay(1000);

    b1 = coef.b1;
    b2 = coef.b2;

    b6 = b5 - 4000;

    x1 = (b2 * (b6 * b6 >> 12)) >> 11; 
    x2 = coef.ac2 * b6 >> 11;
    x3 = x1 + x2;
    long ac1 = coef.ac1;
    b3 = ( (  (ac1<<2) + x3)<<oss + 2) >> 2; // what in data sheet 

    x1 = coef.ac3 * b6 >> 13;
    x2 = (b1 * (b6 * b6 >> 12)) >> 16;
    x3 = ((x1 + x2) + 2) >> 2;
    b4 = (coef.ac4 * (unsigned long) (x3 + 32768)) >> 15;

    b7 = ((unsigned long) up - b3) * (50000 >> oss);

    p = (b7 < 0x80000000) ? (b7 * 2) / b4 : (b7 / b4) * 2;

    x1 = (p >> 8) * (p >> 8);
    x1 = (x1 * 3038) >> 16;
    x2 = (-7357 * p) >> 16;
    p = p + ((x1 + x2 + 3791) >> 4);

    //Serial.print( "p=");
    //Serial.print( p/10 );
    //Serial.print( "." );
    //Serial.print( p%10 );
    //Serial.println( " hPA" );

    float fp = p;
    fp = fp * 10.0;
    sendData("-BMP-pres",fp,"Pa");
    delay(1000);
  }

  delay(30000);
  delay(20000);
}

















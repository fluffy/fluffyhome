

#include <PString.h>
#include <OneWire.h>

/* DS18S20 Temperature chip i/o */

OneWire  ds(8);  // on pin 8


void setup(void) 
{
  Serial.begin(9600);
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


void loop(void) 
{
  byte i;
  byte present = 0;
  byte data[20];
  byte addr[8];

  if ( !ds.search(addr)) 
  {
    //Serial.print("No more addresses.\n");
    ds.reset_search();
    delay(2000);
    return;
  }

  Serial.print("Fam=");
  Serial.print(addr[0]/16, HEX);
  Serial.print(addr[0]%16, HEX);

  Serial.print(" Ser=");
  for( i = 1; i < 7; i++)
  {
    Serial.print(addr[i]/16, HEX);
    Serial.print(addr[i]%16, HEX);
  }
  Serial.print(" ");

  if ( OneWire::crc8( addr, 7) != addr[7]) 
  {
    Serial.println("BAD CRC in address");
    return;
  }

  if ( addr[0] == 0x10) 
  {
    Serial.print("Found DS18S20 Temperature ");

    ds.reset();
    ds.select(addr);
    ds.write(0x44,1);         // start conversion, with parasite power on at the end

    delay(750);    

    ds.reset();
    ds.select(addr);    
    ds.write(0xBE);         // Read Scratchpad

    for ( i = 0; i < 9; i++) 
    {          
      data[i] = ds.read();
    }
    if ( OneWire::crc8( data, 8) != data[8] )
    {
      Serial.print("BAD CRC in Temperature");
    }

    int temp2x = (data[1]<<8) + data[0];
    int temp16x = (temp2x>>1)*16 - 4 + 16 - data[6] ;
    float temp= temp16x/16.0;

    Serial.print(" Temp=");
    Serial.print( temp );

    Serial.println();

    char bufStore[64];
    PString data(bufStore, sizeof(bufStore));

    data += "{ \"n\":\"1wr:";
    for( i = 1; i < 7; i++)
    {
      data.print(addr[i]/16, HEX);
      data.print(addr[i]%16, HEX);
    }  
    data += "\" ";
    data += ", \"v\":"; 
    data += temp ;
    data += " }";

    Serial.println( data );
  }

  if ( addr[0] == 0x89) 
  {
    Serial.print("Found DS2502-E48 MAC address ");

    ds.reset();
    ds.select(addr);

    ds.write(0xF0); // read memory      
    ds.write(0x00); // addr low     
    ds.write(0x00); // addr high      

    int ack = ds.read();

    for ( i = 0; i < 13; i++)
    {          
      data[i] = ds.read();
    }

    // comput the CRC-16
    //unsigned int crc = ds.crc16( (unsigned short*)data, 0x0b/2 ); // this does not work 
    unsigned int crc = crc16( data, 0x0B );
    unsigned int icrc = (data[0x0c]<<8) + data[0x0b];
    if ( ~icrc != crc )
    {
      Serial.print("BAD CRC - EUI48 data");
    }

    Serial.print(" MAC:");
    for ( i = 10; i > 4; i--)
    {          
      Serial.print(data[i]/16, HEX);
      Serial.print(data[i]%16, HEX);
    }
    Serial.println("");  
  }

}
















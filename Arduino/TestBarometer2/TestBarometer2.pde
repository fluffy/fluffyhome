

// Code by cullen from rev 1.2 of data sheet 
#include <Wire.h>

const int bmp085Addr = 0x77;


struct  
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


void setup()
{  
  Serial.begin(9600);  

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


void loop()
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
  Serial.print( "ut=");
  Serial.println( ut );

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

  Serial.print( "up=");
  Serial.println( up );

  // compute temp and pressure 
  long x1, x2, b5, t, b6, x3, b3, p , b1, b2;
  unsigned long  b4, b7;

  x1 = ((long)ut - coef.ac6) * coef.ac5 >> 15;
  x2 = ((long) coef.mc << 11) / (x1 + coef.md);
  b5 = x1 + x2;
  t = (b5 + 8) >> 4;

  Serial.print( "t=");
  Serial.print( t/10 );
  Serial.print( "." );
  Serial.print( t%10 );
  Serial.println( " C" );

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

  Serial.print( "p=");
  Serial.print( p/10 );
  Serial.print( "." );
  Serial.print( p%10 );
  Serial.println( " hPA" );

  delay( 2000 );

}










#include <Wire.h>

const unsigned char i2cAddr = 0x42;
unsigned char readReg = 0; // register to use for next read 

const int numReg=2;
unsigned long regVal[numReg]; 


void setup()
{
  Wire.begin(i2cAddr);   
  Wire.onRequest(i2cBusRead);
  Wire.onReceive(i2cBusRecv);

  for ( int i=0; i<numReg; i++ ) {
    regVal[i]=0;
  }

  regVal[0] = 0x12345678;
  regVal[1] = 0x9ABCDEF0;
}


void loop()
{
  delay(1000);
  regVal[0]++;
  
}


void i2cBusRecv(int num)
{
  readReg = Wire.read();
  if ( readReg  >= numReg) {
    readReg = 0;
  }
}


void i2cBusRead()
{
  //noInterrupts() ;
  unsigned long data = regVal[readReg];
  //interrupts();

  Wire.write( (char*)(&data), sizeof( data ) ); 
}

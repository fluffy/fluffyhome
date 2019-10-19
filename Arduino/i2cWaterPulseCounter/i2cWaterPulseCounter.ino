#include <EEPROM.h>
#include <Wire.h>

const char* version = "Fluffy Pulse Counter ver 1.03";

// arduino eeprom rted at 100k write cycles
const unsigned long minEepromTime = 3600000ul; // (1hour) min time bewteen eeprom write in ms

const int sensorPin0 = 2;   // water meter input used for interupt zero
const int sensorPin1 = 3;   // water meter input used for interupt one

const unsigned char i2cAddr = 0x42;
unsigned char readReg = 0; // register to use for next read

const unsigned long bounceTime[2] = {
  2, 2
}; // de bounce time for sensor in ms


const int numReg = 2;
unsigned long regVal[numReg];

volatile unsigned long count[2];     // counter
volatile unsigned long prevTime[2]; // time counter was last sent

unsigned long prevEepromCount[2]; // last value in EEPROM
unsigned long prevEepromTime[2];  // time of last write to EEPROM

void checkUpdateEeprom(int ch)
{
  unsigned long now = millis();

  if ( now > prevEepromTime[ch] + minEepromTime )
  {
    if ( (regVal[ch] != prevEepromCount[ch])  )
    {
      unsigned long c = regVal[ch];

      storeEEPROM( c, ch);
      prevEepromCount[ch] = c;
      prevEepromTime[ch] = now;
    }
  }
}


void storeEEPROM( unsigned long count , int ch )
{
  Serial.println( "Write to EEPROM" );

  EEPROM.write( 0 + ch * 4, (byte)count );
  count = count >> 8;
  EEPROM.write( 1 + ch * 4, (byte)count );
  count = count >> 8;
  EEPROM.write( 2 + ch * 4, (byte)count );
  count = count >> 8;
  EEPROM.write( 3 + ch * 4, (byte)count );
}


unsigned long loadEEPROM(int ch)
{
  unsigned long count = 0;
  count = count + EEPROM.read( 3 + ch * 4);
  count = count << 8;
  count = count + EEPROM.read( 2 + ch * 4);
  count = count << 8;
  count = count + EEPROM.read( 1 + ch * 4);
  count = count << 8;
  count = count + EEPROM.read( 0 + ch * 4);

  return count;
}


void setup()
{
  Serial.begin(115200);
  delay(100);
  Serial.println();
  Serial.println( version );

#if 0
  // initialze values in EEPROM
  count[0] = 1; storeEEPROM( count[0], 0 );
  count[1] = 1; storeEEPROM( count[1], 1 );
#endif

  count[0] = loadEEPROM(0);
  count[1] = loadEEPROM(1);

  unsigned long now = millis();
  prevTime[0] = now;
  prevTime[1] = now;

  regVal[0] = count[0];
  regVal[1] = count[1];

  prevEepromCount[0] = count[0];
  prevEepromCount[1] = count[1];

  prevEepromTime[0] = now;
  prevEepromTime[1] = now;

  Wire.begin(i2cAddr);
  Wire.onRequest(i2cBusRead);
  Wire.onReceive(i2cBusRecv);

  pinMode(sensorPin0, INPUT_PULLUP);
  pinMode(sensorPin1, INPUT_PULLUP);

  attachInterrupt(0, sensorInt0 , RISING);
  attachInterrupt(1, sensorInt1 , RISING);
}


void sensorInt(int ch)
{
  unsigned long now = millis();
  if ( now > prevTime[ch] + bounceTime[ch] )
  {
    count[ch]++;
    prevTime[ch] = now;
  }

  if ( prevTime[ch] > now )
  {
    prevTime[ch] = now;
  }
}


void sensorInt0()
{
  sensorInt( 0 );
}


void sensorInt1()
{
  sensorInt( 1 );
}


void loop()
{
  // evrery 100 ms copy current count to register for i2C read
  delay(90);
  noInterrupts() ;
  regVal[0] = count[0];
  interrupts() ;

  delay(10);
  noInterrupts();
  regVal[1] = count[1];
  interrupts();

  checkUpdateEeprom( 0 );
  checkUpdateEeprom( 1 );

#if 1
  static int loopCount = 0;
  if ( (loopCount++ % 10) == 0 ) {
    Serial.print( "time=" ); Serial.print( millis() / 1000 ) ; Serial.print( " -> " );
    Serial.print( regVal[0] , HEX ); Serial.print(' ');  Serial.println( regVal[1] , HEX );
  }
#endif
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
  unsigned long data = regVal[readReg];
  byte checkSum = 0x42;
  checkSum ^= data;
  checkSum ^= data>>8;
  checkSum ^= data>>16;
  checkSum ^= data>>24;
  Wire.write( (char*)(&data), sizeof( data ) );
  Wire.write( checkSum );
}

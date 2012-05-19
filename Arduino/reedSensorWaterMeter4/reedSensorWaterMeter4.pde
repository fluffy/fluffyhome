//#include <MsTimer2.h>
#include <EEPROM.h>
#include <PString.h>

const char* version = "Fluffy Water Meter ver 0.01";

const int sensorPin0 = 2;   // water meter input used for interupt zero 
const int sensorPin1 = 3;   // water meter input used for interupt one 
//const int ledPin =  13;    // the number of the LED pin
//const int powerPin =  7;    // the number of the LED pin
//const int flashPin = 12; // second LED to flash 

const unsigned long bounceTime[2] = { 
  200, 10 }; // de bounce time for sensor in ms 

const unsigned long maxSendTime   =  30000; // max time bewteen sends in ms 
const unsigned long minSendTime   =   5000; // min time bewteen sends in ms 
const unsigned long minEepromTime = 600000; // min time bewteen eeprom write  

const float litresPerPulse[2] = { 
  3.785, 0.001 };

volatile unsigned long globalCount[2];     // counter 
volatile unsigned long prevTime[2]; // time counter was last sent
volatile unsigned long prevCount[2]; // value of counter when last sent
volatile unsigned long prevEepromTime[2];


void setup() 
{
  Serial.begin(9600);
  delay( 1000 );
  Serial.println( version );

  globalCount[0] = loadEEPROM(0);
  //globalCount[0] = 284; storeEEPROM( globalCount[0], 0 );
  prevCount[0] = globalCount[0];

  globalCount[1] = loadEEPROM(1);
  //globalCount[1] = 3; storeEEPROM( globalCount[1], 1 );
  prevCount[1] = globalCount[1];

  unsigned long now;
  now = millis();

  prevEepromTime[0] = now;
  prevTime[0] = now;
  prevEepromTime[1] = now;
  prevTime[1] = now;

  //pinMode(ledPin, OUTPUT);      
  //pinMode(flashPin, OUTPUT);      
  //pinMode(powerPin, OUTPUT);      

  attachInterrupt(0, sensorInt0 , RISING);   
  attachInterrupt(1, sensorInt1 , RISING);   

  //MsTimer2::set( 500 /* ms */, checkDataToSend ); 
  //MsTimer2::start();  

  //digitalWrite(powerPin, HIGH);  
}


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


void loop()
{
  delay(500);

  //Serial.println( globalCount[0] );
  //Serial.println( globalCount[1] );

  checkDataToSend(0);
  checkDataToSend(1);
}


void checkDataToSend(int ch)
{
  static byte flash=0;

  unsigned long now;

  now = millis();
  //digitalWrite(flashPin, ( (flash++)%2) ? HIGH : LOW);  

  if ( (globalCount[ch] != prevCount[ch]) || ( now > prevTime[ch] + maxSendTime ) )
  {
    if ( now > prevTime[ch] + minSendTime )
    {
      sendData( globalCount[ch], now-prevTime[ch], globalCount[ch]-prevCount[ch], ch );
      prevTime[ch] = now;

      if (globalCount[ch] != prevCount[ch])
      {

        if ( now > prevEepromTime[ch] + minEepromTime )
        {
          storeEEPROM(globalCount[ch],ch);  
          prevEepromTime[ch] = now;
        }
        prevCount[ch] = globalCount[ch];
      }

    }
  }
}


void sendData( unsigned long count,  unsigned long deltaTime,  unsigned long deltaCount , int ch )
{
  char bufStore[80];
  PString data(bufStore, sizeof(bufStore));

  float volume = float(count);
  volume *= litresPerPulse[ch]; //convert to litres

  float flow =0.0;
  if ( ( deltaTime > 1000 ) && (deltaTime < 600000 ) )
  {
    flow = float(deltaCount);
    flow *= litresPerPulse[ch]; // convert from to litres
    float dt = float(deltaTime) / 1000.0 ; // convert to seconds 
    flow = flow / dt;
  }

  data += "{\"m\":[{ \"n\":\"ZB-0013A2004052";
  if ( ch != 0 )
  {
    data += "-ch";
    data += ch;
  }
  data += "\",\"v\":"; 
  data += flow ;
  data += ",\"s\":"; 
  data += volume ;
  data += ",\"u\":\"lps\"}]}";

  Serial.println( data );
  delay( 1000 );
}


void sensorInt(int ch)
{
  unsigned long now;

  now = millis();
  if ( now > prevTime[ch] + bounceTime[ch] )
  { 
    globalCount[ch]++;

    //digitalWrite(ledPin, (globalCount[ch]%2)?HIGH:LOW);        
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






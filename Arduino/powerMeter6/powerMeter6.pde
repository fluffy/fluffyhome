
#include <PString.h>
#include <Ethernet.h>
#include <EthernetDHCP.h>
#include <EthernetDNS.h>
#include <EEPROM.h>

// todo - better way to get MAC addr
// todo - what happens if ethernet, dns, ip etc fails 
// periodic reset would be nice
// how to calibrate ?
// led to indicate status 


byte mac[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0x66, 0xED };


const unsigned long maxSendTime   =  60000; // max time bewteen sends in ms 
const unsigned long minSendTime   =  15000; // min time bewteen sends in ms 
const unsigned long minEepromTime = 600000; // min time bewteen eeprom write  

const int vSensorPin = 0;    // analog pin for voltage sensor
const int cSensorPin = 1;    // analog pin for current sensor

const float vScale = 0.4336545;
const float aScale  = 0.0333718;
float vOffset = -509.80;
float aOffset  = -510.89;


float vSum=0.0;
float vSumSq=0.0;
float vMin=0.0;
float vMax=0.0;

float aSum=0.0;
float aSumSq=0.0;
float aMin=0.0;
float aMax=0.0;

float wSum=0.0;

unsigned long sampleTime;
unsigned long prevSampleTime;

unsigned int count=0;

unsigned int power=0; // current power level in watts 
unsigned long energy=0; // total accumulated energy in joules

//const char* serverName = "wwww.fluffyhome.com"; // double CNAME lookup 
const char* serverName = "g.fluffyhome.com"; // direct A record lookup 
byte ipAddrServer[4];


#define CRLF "\r\n"



void setup() 
{
  Serial.begin(9600);
  delay( 1000 );

  // Note: Ethernet shield uses digitial IO pins 10,11,12, and 13   

  Serial.println("DHCP getting IP address ..");
  EthernetDHCP.begin(mac);

  // Since we're here, it means that we now have a DHCP lease, so we print
  // out some information.
  const byte* ipAddr = EthernetDHCP.ipAddress();
  const byte* gatewayAddr = EthernetDHCP.gatewayIpAddress();
  const byte* dnsAddr = EthernetDHCP.dnsIpAddress();

  Serial.print("IP Address is ");
  printIP(ipAddr);

  Serial.print(CRLF "Gateway: ");
  printIP(gatewayAddr);

  Serial.print(CRLF "DNS server: ");
  printIP(dnsAddr);

  EthernetDNS.setDNSServer(dnsAddr);

  Serial.print(CRLF "Doing DNS lookup of '");
  Serial.print(serverName);
  Serial.println("'");
  DNSError err = EthernetDNS.resolveHostName(serverName, ipAddrServer);

  if (DNSSuccess == err)
  {
    Serial.print("Server IP is: ");
    printIP(ipAddrServer);
    Serial.print( CRLF );
  } 
  else if (DNSTimedOut == err)
  {
    Serial.println("DNS Timed out");
  }
  else if (DNSNotFound == err)
  {
    Serial.println("DNS Does not exist");
  } 
  else 
  {
    Serial.print("DNS Failed with error code ");
    Serial.println((int)err, DEC);
    
    // TODO - what to do? wait few seconds and reset ?
  } 

  sampleTime = millis();
  prevSampleTime = sampleTime;

  energy = loadEEPROM();
  Serial.print("Loaded stored value energy=");
  Serial.println(energy);

  if ( (energy|0xFF) == 0xFFFFffff )
  {
    energy = 0; // reset for unit eeprom 
    storeEEPROM( energy );
  }

}


void sendData()
{
  Client tcp( ipAddrServer , 80 /*port */ );

  //Serial.println("connecting...");

  if (tcp.connect()) 
  {
    //Serial.println("connected");

    char bufStore[128];
    PString data(bufStore, sizeof(bufStore));

    data += "[ { \"n\":\"FluffTestSensor1\" ";
    data += ", \"j\":"; 
    data += energy ;
    data += ", \"v\":"; 
    data += power ;
    data += " } ]" ;

    tcp.print( "POST /sensorValues/ HTTP/1.1" CRLF
      "User-Agent: Power Meter Ver 0.01" " " CRLF
      "Host: www.fluffyhome.com" CRLF // todo fix 
    "Accept: */" "*" CRLF
      "Content-Type: application/senmn+xml" CRLF
      "Content-Length: " );
    tcp.print( data.length() );
    tcp.print( CRLF CRLF );
    tcp.print( data );

    Serial.print( "Data len=" );
    Serial.print( data.length() );
    Serial.print( " is: " );
    Serial.println( data );

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
        Serial.println();
        Serial.println("server disconnected");
        break;
      }
    }

    //Serial.println("tcp disconnecting");
    tcp.stop();
  } 
  else 
  {
    Serial.println("TCP connection failed");
  } 
}


void storeEEPROM( unsigned long count )
{
  //Serial.println( "Write to EEPROM" );

  EEPROM.write( 0 , (byte)count );
  count = count >> 8;
  EEPROM.write( 1 , (byte)count );
  count = count >> 8;
  EEPROM.write( 2 , (byte)count );
  count = count >> 8;
  EEPROM.write( 3 , (byte)count );   
}


unsigned long loadEEPROM()
{
  unsigned long count = 0;
  count = count + EEPROM.read( 3 );
  count = count << 8;
  count = count + EEPROM.read( 2 );
  count = count << 8;
  count = count + EEPROM.read( 1 );
  count = count << 8;
  count = count + EEPROM.read( 0 );

  return count;
}


void waitPosZeroCross()
{
  int vSen;
  unsigned long t = micros();
  t = t + 100000; // 1/10th of a second is max time to wait 

  do // wait for it to go negative 
  {
    vSen = analogRead(vSensorPin);    
  }
  while ( (vSen >= 400) && ( micros() < t ) );

  do // wait for sensor to get to zero or above 
  {
    vSen = analogRead(vSensorPin);    
    // tood could figure out cOffset by tracking zero crossing of voltage 
  }
  while ( (vSen+vOffset < 0 ) && ( micros() < t ) );     
}


void loop()
{
  waitPosZeroCross();
  unsigned long t = micros();
  t = t + 100000; // 1/10th of a second 

  while ( micros() < t )
  {
    sample();
  }
  prevSampleTime = sampleTime;
  sampleTime = millis();

  computeEnergy();

  static int prevPower=0;
  static unsigned long prevTime=0;
  static unsigned long prevEepromTime=0;
  unsigned long now;

  now = millis();
  if ( ( power != prevPower) || ( now > prevTime + maxSendTime ) )
  {
    if ( now > prevTime + minSendTime )
    {
      sendData();
      prevTime = now;

      if ( now > prevEepromTime + minEepromTime )
      {
        storeEEPROM(energy);  
        prevEepromTime = now;

        EthernetDHCP.maintain();
      }
      prevPower = power;
    }
  }

  //delay( 400 );   // TODO remove      
}


void computeEnergy()
{
  if ( count == 0 ) 
  {
    return;
  }

  float n = count;

  float vAvg = vSum / n ;
  float vRMS = sqrt( vSumSq / n );
  float aAvg = aSum / n;
  float aRMS = sqrt( aSumSq / n );  
  float watts = wSum / n;

  unsigned long deltaTime = sampleTime - prevSampleTime;
  float deltaJoules = float(deltaTime) * watts / 1000.0 ;

  energy += int( 0.5+deltaJoules );
  power = int( 0.5+watts );

  Serial.print(" n=");
  Serial.print( count );
  Serial.print(" vAvg=");
  Serial.print( vAvg );

  //Serial.print(" vOff=");
  //Serial.print( vOffset );

  Serial.print(" aOff=");
  Serial.print( aOffset );

  Serial.print(" volts=");
  Serial.print( vRMS );
  //Serial.print(" vMin=");
  //Serial.print( vMin );
  //Serial.print(" vMax=");
  //Serial.print( vMax );

  Serial.print(" ampAvg=");
  Serial.print( aAvg );

  Serial.print(" amps=");
  Serial.print( aRMS );
  Serial.print(" aMin=");
  Serial.print( aMin );
  Serial.print(" aMax=");
  Serial.print( aMax );

  Serial.print(" watts=");
  Serial.print( watts );

  Serial.print(" joules=");
  Serial.print( energy );

  Serial.print(" deltaJoules=");
  Serial.print( deltaJoules );

  Serial.print(" deltaTime=");
  Serial.print( deltaTime );

  Serial.println(" ");

  vSum = 0.0;
  vSumSq = 0.0;
  aSum = 0.0;
  aSumSq = 0.0;
  wSum = 0.0;

  vMin=  1000.0;
  vMax= -1000.0;
  aMin=  1000.0;
  aMax= -1000.0;

  count=0;

  //offsetVolt += 1.0;
  vOffset -= (vAvg/vScale) * 0.1; // DC filter on voltage sensor 
  //aOffset -= (aAvg/aScale) * 0.2; // DC filter on current sensor 

}


void sample()
{
  float v;
  float a;
  float w;

  int vSen=0;
  int aSen=0;

  vSen = analogRead(vSensorPin);    
  aSen = analogRead(cSensorPin);    

  v = float(vSen);
  v += vOffset;
  v *= vScale;

  a = float(aSen) ;
  a += aOffset; 
  a *= aScale;

  w = v * a;

  vSum += v;
  vSumSq += v*v;
  aSum += a;
  aSumSq += a*a;
  wSum += w;

  if ( v < vMin )
  {
    vMin = v;
  }
  if ( v > vMax  )
  {
    vMax = v;
  }

  if ( a < aMin )
  {
    aMin = a;
  }
  if ( a > aMax  )
  {
    aMax = a;
  }

  count += 1.0;

  //  digitalWrite( 11 , ( senV > int(avg) ) ? HIGH : LOW );
  //  digitalWrite( 12 , ( senV > int(avg+rms) ) ? HIGH : LOW );
  // v = int(avg)/2;
  //shiftOut( 9,8,MSBFIRST, v );
}


void printIP(const byte* ip)
{
  char buf[6];
  Serial.print(itoa(ip[0],buf,10));
  Serial.print(".");
  Serial.print(itoa(ip[1],buf,10));
  Serial.print(".");
  Serial.print(itoa(ip[2],buf,10));
  Serial.print(".");
  Serial.print(itoa(ip[3],buf,10));
}







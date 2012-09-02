#include <SPI.h>
#include <Ethernet.h>
#include <EEPROM.h>
#include <PString.h>
#include <OneWire.h>
#include <DNSClient.h>


// This runs with Arduino version 1.0.1 software 
// you need to install PString ver 3 and OneWire libraries



// note the serial port is running at 19.2 Kbps for this one 

#define VERSION  "Fluffy ECM1240 Meter ver 0.06"
const byte debug=1;

const int minPostTime = 15000; // time in ms 
const int maxPostTime = 60000; // time in ms 

byte macAddr[] = { 
  0xDE, 0xAD, 0xBE, 0xEF, 0x66, 0xED };

const char* serverName = "wwww.fluffyhome.com"; // double CNAME lookup 
//const char* serverName = "g.fluffyhome.com"; // direct A record lookup 
//IPAddress ipAddrServer;


#define CRLF "\r\n"


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

void getMacAddr( OneWire& bus, byte addr[8] );
unsigned int crc16( byte* data, int len );


void setup()
{
 delay( 200 );

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
  byte addr[8];
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
 
  if (debug) Serial.println("DHCP getting IP address ...");
  Ethernet.begin(macAddr);

  digitalWrite( rLed, HIGH );  
  digitalWrite( gLed, HIGH );  
  digitalWrite( bLed, LOW );  
  
  // Since we're here, it means that we now have a DHCP lease, so we print
  // out some information.
  if (debug) Serial.print("IP Address is ");
  Serial.println(Ethernet.localIP());

  if (debug) Serial.print(CRLF "Gateway: ");
  Serial.println(Ethernet.gatewayIP());

  if (debug) Serial.print(CRLF "DNS server: ");
  Serial.println(Ethernet.dnsServerIP());

  //EthernetDNS.setDNSServer(dnsAddr);

//  if (debug) Serial.print(CRLF "Doing DNS lookup of '");
//  if (debug) Serial.print(serverName);
//  if (debug) Serial.println("'");
//
//  DNSClient dns;
//  int ret;
//  
//  dns.begin( Ethernet.dnsServerIP());
//  ret = dns.getHostByName(host, ipAddrServer);
//  
//  if (ret == 1)
//  {
//    if (debug) Serial.print("Server IP is: ");
//    if (debug) Serial.println(ipAddrServer);
//  } 
//  else
//  {
//    if (TIMED_OUT == err)
//    {
//      if (debug) Serial.println("DNS Timed out");
//    }
//    else if (INVALID_SERVER == err)
//    {
//      if (debug) Serial.println("DNS Does not exist");
//    } 
//    else 
//    {
//      if (debug) Serial.print("DNS Failed with error code ");
//      if (debug) Serial.println((int)err, DEC);
//    } 
//
//    digitalWrite( rLed, HIGH );  
//    digitalWrite( gLed, LOW );  
//    digitalWrite( bLed, HIGH );  
//
//    // TODO - what to do? wait few seconds and reset ?
//    delay( 15000 );
//
//    digitalWrite( rLed, LOW );  
//    digitalWrite( gLed, LOW );  
//    digitalWrite( bLed, LOW );
//
//    delay( 500 );
//    goto restart;
//  }

  digitalWrite( rLed, LOW );  
  digitalWrite( gLed, LOW );  
  digitalWrite( bLed, HIGH );  
}


void sendData(unsigned long energy, unsigned long power)
{
  digitalWrite( bLed, HIGH );  
  digitalWrite( gLed, LOW );  
  digitalWrite( rLed, LOW );  

  EthernetClient tcp;

  //Serial.println("connecting...");
  if ( tcp.connect(serverName , 80 /*port */) ) 
  {
    //Serial.println("connected");

    char bufStore[128];
    PString data(bufStore, sizeof(bufStore));

    data += "{\"m\":[{ \"n\":\"MAC";
    for( int i = 0; i < 6; i++)
    {
      data.print(macAddr[i]/16, HEX);
      data.print(macAddr[i]%16, HEX);
    }  
    data += "-ch0\", \"v\": "; 
    data += power ;
    data += ", \"s\": "; 
    data += energy ;
    data += " , \"u\":\"W\" }]}";

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


void filterData(unsigned long energy, unsigned long power)
{
  static unsigned long prevTime=0;
  unsigned long now = millis();
  static unsigned long prevPower=0;

  byte doPost =0;

  if ( now - prevTime < minPostTime )
  {
    return;
  }
  if ( now - prevTime > maxPostTime )
  {
    doPost = 1;
  }
  if ( abs( prevPower - power) > 30 )
  {
    doPost = 1;
  }

  if ( doPost )
  {
    sendData( energy,  power);
    prevTime = now;
    prevPower = power;
  }
}


void processMsg( byte msg[] , int len )
{
  int voltageX10   = (msg[1]<<8) + msg[2];

  int current0X100 = msg[31] + (msg[32]<<8) ;
  int current1X100 = msg[33] + (msg[34]<<8) ;

  unsigned long energy0     = msg[3 ] + (msg[4 ]<<8) + (msg[5 ]<<16) + (msg[6 ]<<24); //+ ( ((long long)msg[ 7])<<32);
  unsigned long energy1     = msg[8 ] + (msg[9 ]<<8) + (msg[10]<<16) + (msg[11]<<24);// + ( ((long long)msg[12])<<32);

  if (debug) Serial.print("Voltage = "); 
  if (debug) Serial.println( float(voltageX10)/10.0 );
  if (debug) Serial.print("Current = "); 
  if (debug) Serial.println( float(current0X100)/100.0 );
  if (debug) Serial.print("Energy0 ="); 
  if (debug) Serial.println( energy0 );

  if ( current0X100 < 0 ) current0X100=0;
  if ( current1X100 < 0 ) current1X100=0;
  if ( voltageX10 < 0 ) voltageX10=0;

  unsigned long power = voltageX10;
  power *=  current0X100;
  power /= 1000;
  unsigned long energy = energy0;

  if (debug) Serial.print("Power ="); 
  if (debug) Serial.println( power );
  if (debug) Serial.print("Energy ="); 
  if (debug) Serial.println( energy );

  filterData( energy , power );
}


void loop()
{
  sendData( 22 , 55 );
}

void loopReel()
{
  if (Serial.available() > 0) 
  {
    static byte curr=0;
    static byte prev=0;

    prev = curr;
    curr = Serial.read();
    //Serial.println( (int)curr );

    if ((prev != 0xFE) || (curr != 0xFF))
    {
      return; // keep looking for start sync 
    }
    //Serial.println("Found Start Sync");
    byte cSum = 0xFF + 0xFE;

    byte buf[128];
    int len=0;

    do
    {
      while ( Serial.available() == 0 )
      {
        delay(500);
      }
      prev = curr; 
      curr = Serial.read();
      //fprintf(stderr," %02x",d);
      buf[len++] = curr;
      if ( len >= sizeof(buf)-1 )
      {
        if (debug) Serial.println("Message is too large\n");
        return;  
      }
      cSum += curr;
    }
    while ( (prev!=0xFF) || (curr!=0xFE) );
    //Serial.println("Found End Sync");

    while ( Serial.available() == 0 )
    {
      delay(500);
    }
    byte check = Serial.read();

    if ( check != cSum )
    {
      if (debug) Serial.println( "Bad checksum in RS232 data from ECM1240" );
      if (debug) Serial.println( (int)check , HEX);
      if (debug) Serial.println( (int)cSum , HEX );
      if (debug) Serial.println( (int)( cSum - check ) , HEX  );

      return;
    }

    digitalWrite( rLed, LOW );  
    digitalWrite( gLed, HIGH );  
    digitalWrite( bLed, LOW );  

    //Serial.println("Found ECM Message");
    //Serial.print( "len=" ); 
    //Serial.println( len);
    
    processMsg( buf , len );
  }
}

//
//void printIP(const byte* ip)
//{
//  char buf[6];
//  if (debug) Serial.print(itoa(ip[0],buf,10));
//  if (debug) Serial.print(".");
//  if (debug) Serial.print(itoa(ip[1],buf,10));
//  if (debug) Serial.print(".");
//  if (debug) Serial.print(itoa(ip[2],buf,10));
//  if (debug) Serial.print(".");
//  if (debug) Serial.print(itoa(ip[3],buf,10));
//}


void getMacAddr( OneWire& bus, byte addr[8] )
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















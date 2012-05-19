
// ideas from from http://www.ragingreality.com/%7Ewprasek/serial_temp_humidity.pde


int busCdataPin = 4;
int busCClkPin = 5;


void resetSHT()
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


//Specific SHT start command
void startSHT()
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


void writeByteSHT(byte data)
{ 
  pinMode(busCClkPin,OUTPUT);
  pinMode(busCdataPin,OUTPUT);  

  //  digitalWrite(busCdataPin,LOW);
  shiftOut(busCdataPin,busCClkPin,MSBFIRST,data);

  pinMode(busCdataPin,INPUT);

  //Wait for SHT15 to acknowledge by pulling line low
  while(digitalRead(busCdataPin) == 1);

  digitalWrite(busCClkPin,HIGH);
  digitalWrite(busCClkPin,LOW);  //Falling edge of 9th clock

  //wait for SHT to release line
  while(digitalRead(busCdataPin) == 0 );

  //wait for SHT to pull data line low to signal measurement completion
  //This can take up to 210ms for 14 bit measurments
  int i = 0;
  while(digitalRead(busCdataPin) == 1 )
  {
    i++;
    if (i == 255) break;

    delay(10);
  } 

  //debug
  i *= 10;
  //Serial.print("Response time = ");
  //Serial.println(i);
}


//Read 16 bits from the SHT sensor
int readByte16SHT()
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
      //      Serial.print(temp,BIN);
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

  //leave clock high??
  digitalWrite(busCClkPin,HIGH);

  //  Serial.println();

  return cwt;
}



void setup() 
{
  pinMode(busCdataPin,OUTPUT);
  pinMode(busCClkPin,OUTPUT);

  Serial.begin(9600);        // connect to the serial port

  Serial.println("Resetting SHT...");
  resetSHT();
}


void loop () 
{
  delay(2000);

  Serial.println("Starting Temperature/Humidity reading...");
  
  startSHT();
  writeByteSHT(B0000011);
  int x= readByte16SHT();
  Serial.print("Tempature: ");
  //Serial.println(x);
  float t = -39.65 + 0.01 * float( x );
  Serial.println( t );


  startSHT();
  writeByteSHT(B00000101);
  x = readByte16SHT();
  Serial.print("Humidity: ");
  //Serial.println(x);  
  float rh = -2.0468 + 0.0367 * float( x ) - 1.5955e-6 * float(x) * float(x) ;
  float tc = ( t - 25.0 ) * (0.01 + 0.00008 * float(x) );
  rh += tc;
  Serial.println(rh);  
  //Serial.println(tc);  
}


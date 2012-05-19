
// Ethernet  uses digitial IO pins 10,11,12, and 13   
// PWM can be on pins 3,5,6,9,10,11
// PWM is flakey on 5,6 due to timer interaction
// interupts can happend on pin 2 and 3
// TWI aka I2C is on anlog pins 4 and 5 


int analogPin = 3;

void setup()
{
  Serial.begin(9600);
}


void loop()
{
  float x = float( analogRead(analogPin) )/1024.0; 
  
  Serial.print("x=");
  Serial.print(x);

  float rh = (x - 0.16) * 161.09;

  Serial.print( " RH=" );
  Serial.print( rh );

  Serial.println( "" );
  delay( 2000 );
}


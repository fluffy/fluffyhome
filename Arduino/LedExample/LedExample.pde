

// Ethernet  uses digitial IO pins 10,11,12, and 13   
// PWM can be on pins 3,5,6,9,10,11
// PWM is flakey on 5,6 due to timer interaction
// interupts can happend on pin 2 and 3
// TWI aka I2C is on anlog pins 4 and 5 



int rLed = 5;
int gLed = 6;
int bLed = 9;

void setup() 
{
  pinMode( rLed, OUTPUT );
  pinMode( gLed, OUTPUT );
  pinMode( bLed, OUTPUT );

  digitalWrite( rLed, LOW );  
  digitalWrite( gLed, LOW );  
  digitalWrite( bLed, LOW );  
}

void loop() 
{
  static unsigned int x=0;

  if (0)
  {
    analogWrite(rLed, x);  
    analogWrite(gLed, x);  
    analogWrite(bLed, x/2);  

    x++;
    x = x & 0xFF;
    delay( 4*2 );
  }

  if (0)
  {
    digitalWrite(rLed, (x&1)?HIGH:LOW );  
    digitalWrite(gLed, (x&2)?HIGH:LOW );  
    digitalWrite(bLed, (x&4)?HIGH:LOW );  

    x++;
    delay( 2000 );
  }

  if (1)
  {
    switch (x)
    {
    case 0: // off
      digitalWrite( rLed, LOW );  
      digitalWrite( gLed, LOW );  
      digitalWrite( bLed, LOW );  
      break;

    case 1: // red 
      digitalWrite( rLed, HIGH );  
      digitalWrite( gLed, LOW );  
      digitalWrite( bLed, LOW );  
      break;

    case 2: // green
      digitalWrite( rLed, LOW );  
      digitalWrite( gLed, HIGH );  
      digitalWrite( bLed, LOW );  
      break;

    case 3: // blue
      digitalWrite( rLed, LOW );  
      digitalWrite( gLed, LOW );  
      digitalWrite( bLed, HIGH );  
      break;

    case 4: // magenta 
      digitalWrite( rLed, HIGH );  
      digitalWrite( gLed, LOW );  
      digitalWrite( bLed, HIGH );  
      break;
    }

    x = (x+1)%5;
    delay( 2000 );
  }

}










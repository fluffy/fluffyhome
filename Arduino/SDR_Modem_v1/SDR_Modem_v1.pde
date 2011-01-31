
#define CRLF "\r\n"


const int inputA = A0; 
const int inputB = A1; 
const int inputC = A2; 
const int inputD = A3; 

const int aOutPin = 5;
const int pOutPin = 6;

const int lOutPin = 2;

void setup() 
{
  Serial.begin(19200); 
  pinMode(lOutPin, OUTPUT); 
}

void loop() 
{
  int s1,s2,s3,s4;
  float i,q;
  float a,p;
  int amp,phase;
  
  digitalWrite(lOutPin, HIGH);
  s1 = analogRead(inputA);            
  s2 = analogRead(inputB);            
  s3 = analogRead(inputC);            
  s4 = analogRead(inputD);               
  digitalWrite(lOutPin, LOW); 

  i = s1-s3;
  q = s2-s4;
  
  a = sqrt( i*i + q*q );
  p=0.0;
  if ( a > 0.0 ) {
      float x;
      x = i * 100.0 / a;
      p = atan2(i,q)*180/PI;
  }
  
  
  Serial.print(" i=" ); Serial.print(i);      
  Serial.print(" q=" ); Serial.print(q);      
  Serial.print(" a=" ); Serial.print(a);      
  Serial.print(" p=" ); Serial.print(p);      
  Serial.print(CRLF);
  
  amp = map(512+s1-s3, 0, 1023, 0, 255);   
  phase = map(512+s2-s3, 0, 1023, 0, 255);   

  analogWrite(aOutPin, amp);       
  analogWrite(pOutPin, phase);       

  delay(100);             
}




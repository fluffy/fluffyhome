
void setup()
{
  Serial.begin(19200);
  
  
}

void loop()
{
  if (Serial.available() > 0) 
  {
    byte b =  Serial.read();
    Serial.println( int( b ) , HEX);
  }
}

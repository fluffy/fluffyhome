
void setup()
{
  Serial.begin(9600);
  Serial1.begin(19200);
}


void processMsg( byte msg[] , int len )
{

  int voltageX10   = (msg[1]<<8) + msg[2];
  int current0X100 = msg[31] + (msg[32]<<8) ;
  int current1X100 = msg[33] + (msg[34]<<8) ;

  long energy0     = msg[3 ] + (msg[4 ]<<8) + (msg[5 ]<<16) + (msg[6 ]<<24); //+ ( ((long long)msg[ 7])<<32);
  long energy1     = msg[8 ] + (msg[9 ]<<8) + (msg[10]<<16) + (msg[11]<<24);// + ( ((long long)msg[12])<<32);

  Serial.print("Voltage x10="); Serial.println( voltageX10 );
  Serial.print("Current x100="); Serial.println( current0X100 );
  Serial.print("Energy ="); Serial.println( energy0 );
}


void loop()
{
  if (Serial1.available() > 0) 
  {
    static byte curr=0;
    static byte prev=0;

    prev = curr;
    curr = Serial1.read();
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
      while ( Serial1.available() == 0 )
      {
        delay(500);
      }
      prev = curr; 
      curr = Serial1.read();
      //fprintf(stderr," %02x",d);
      buf[len++] = curr;
      if ( len >= sizeof(buf)-1 )
      {
        Serial.println("Message is too large\n");
        return;  
      }
      cSum += curr;
    }
    while ( (prev!=0xFF) || (curr!=0xFE) );
    //Serial.println("Found End Sync");

    while ( Serial1.available() == 0 )
    {
      delay(500);
    }
    byte check = Serial1.read();

    if ( check != cSum )
    {
      Serial.println( "Bad checksum in RS232 data from ECM1240" );
      Serial.println( (int)check , HEX);
      Serial.println( (int)cSum , HEX );
      Serial.println( (int)( cSum - check ) , HEX  );

      return;
    }

    //Serial.println("Found ECM Message");
    //Serial.print( "len=" ); 
    //Serial.println( len);

    processMsg( buf , len );
  }
}










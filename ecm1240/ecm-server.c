/* 
   Copyright Cullen Jennings 2009,2010 

*/

#include <sys/types.h>   
#include <sys/socket.h>  
#include <arpa/inet.h>   
#include <unistd.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

unsigned char cchar = 0;
unsigned char pchar = 0;
unsigned char checkSum = 0;


unsigned char
getChar( int sock )
{
   unsigned char buf[1];
   size_t numRead = read(sock, buf, sizeof(buf) );
   
   if (numRead != 1 )
   {
      fprintf(stderr, "error in read\n");
      exit(EXIT_FAILURE);
   }
   
   pchar = cchar;
   cchar = buf[0];
   
   checkSum += buf[0];
   
   return buf[0];
}


void
postValue( char* name , float value )
{
   fprintf(stderr,"Post %s = %f \n",name,value);

   char buf[1024];
   snprintf(buf,sizeof(buf),"curl --request PUT --data '%f' http://www.fluffyhome.com/sensor/fluffy/%s/value/",value,name);
   
   //fprintf(stderr,"\n%s\n\n",buf );

   int err = system( buf );
  
   if ( err != 0 )
   {
      fprintf(stderr,"System call to '%s' return value was %d\n",buf,err );
   }
}


void 
processValues(  unsigned int seconds , unsigned int ch1wattSec, unsigned int voltsX10 )
{
   static unsigned int pseconds=0;
   static unsigned int pch1wattSec=0;
   static float pWatts = 0.0;
   
   int dSeconds = seconds - pseconds;
   int dCh1wattSec = ch1wattSec - pch1wattSec;
   
   if ( dSeconds <= 0 ) goto end;
   if ( dSeconds > 65 ) goto end;

   if (dCh1wattSec <= 0 ) goto end;
   if (dCh1wattSec > 100*240*dSeconds ) goto end;
   
   float watts = (float)(dCh1wattSec) / (float)(dSeconds);
    
   //fprintf(stderr,"Usage kW = %f \n", watts/1000.0 );
   
   float dWatts = watts - pWatts;
   if ( dWatts < 0.0 ) 
   {
      dWatts = 0.0 - dWatts;
   }
   
   if ( dWatts < 10.0 )
   {
      if ( dSeconds < 15 )
      {
         return;
      }
   }
   
   postValue( "totalElec" , watts );
   pWatts = watts;
   
  end:
   pseconds=seconds;
   pch1wattSec=ch1wattSec;
}

void
processMsg( int len,  unsigned char msg[] )
{
   if (0)
   {
      fprintf(stderr,"Msg: ");
      int i;
      for ( i=0; i<len; i++ )
      {
         fprintf(stderr," %d:%02x",i,msg[i]);
      }
      fprintf(stderr,"\n");
   }
   
   if ( msg[0] == 3 )
   {
      /* easiest way to sort these out is create a fake message with a bit set
      at the location in question and send it to the normal ECM software and see
      where it shows up in the output data */

      unsigned int ch1ampsX100 = msg[31] + msg[32]*256;
      //fprintf( stderr, "ch1amps x100 = %d \n", ch1ampsX100 );

      unsigned int ch2ampsX100 = msg[33] + msg[34]*256;
      //fprintf( stderr, "ch2amps x100 = %d \n", ch2ampsX100 );

      unsigned int voltsX10 = msg[1]*256 + msg[2];
      //fprintf( stderr, "volts x10 = %d \n", voltsX10 );

      unsigned int dcVoltsX100 = msg[58] + msg[59]*256;
      //fprintf( stderr, "dcVolts x100 = %d \n", dcVoltsX100 );

      unsigned int ch1wattSec = msg[3] + msg[4]*256 + msg[5]*256*256 + msg[6]*256*256*256;
      //fprintf( stderr, "ch1wattSec %d \n", ch1wattSec );
      unsigned int ch2wattSec = msg[8] + msg[9]*256 + msg[10]*256*256 + msg[11]*256*256*256;
      //fprintf( stderr, "ch2wattSec %d \n", ch2wattSec );
      unsigned int ch1wattSecPolar = msg[13] + msg[14]*256 + msg[15]*256*256 + msg[16]*256*256*256;
      //fprintf( stderr, "ch1wattSec %d \n", ch1wattSecPolar );
      unsigned int ch2wattSecPolar = msg[18] + msg[19]*256 + msg[20]*256*256 + msg[21]*256*256*256;
      //fprintf( stderr, "ch1wattSec %d \n", ch2wattSecPolar );

      unsigned int seconds = msg[35] + msg[36]*256 + msg[37]*256*256;
      //fprintf( stderr, "seconds %d \n", seconds );

      processValues( seconds, ch1wattSec, voltsX10 );
   }
}


void
processData( int sock )
{
   int c;
   
   while (1)
   {
      unsigned char msgBuf[128];
      int msgPos =0;
      
      //fprintf(stderr,"\n\nSyncing .... ");
      do
      {
         unsigned char d = getChar( sock );
         //fprintf(stderr," %02x",d);
      }  
      while ( (pchar!=0xFE) || (cchar!=0xFF) ); // find the start sync 
      //fprintf(stderr," ... FOUND\n");
      checkSum = (unsigned char)(0xFD);
            
      //fprintf(stderr,"Message:");
      do
      {
         unsigned char d = getChar( sock );
         //fprintf(stderr," %02x",d);
         msgBuf[msgPos++]=d;
         if ( msgPos >= sizeof(msgBuf)-1 )
         {
            fprintf(stderr,"Message is too large\n");
            continue; // go back to looking for sync, msg too large 
         }
      }
      while ( (pchar!=0xFF) || (cchar!=0xFE) ); // find the end sync 
      unsigned char sum = checkSum;
      unsigned char check = getChar( sock );
      //fprintf(stderr," check=%02x sum=%02x \n",check,sum);

      if ( check == sum )
      {
         processMsg( msgPos-2 , msgBuf );
      }
      else
      {
         fprintf(stderr,"Bad check sum. check=%02x sum=%02x \n",check,sum);
      }
      
   }
}


int 
main(int argc, char* argv[] )
{
   int listenPort = 8083;
   int lSock = 0;
   int dataSock = 0;
   struct    sockaddr_in saddr;

    if ( (lSock = socket(AF_INET, SOCK_STREAM, 0)) < 0 ) 
    {
       fprintf(stderr, "Listen failed\n");
       exit(EXIT_FAILURE);
    }
    
    memset(&saddr, 0, sizeof(saddr));
    saddr.sin_port        = htons(listenPort);
    saddr.sin_family      = AF_INET;
    saddr.sin_addr.s_addr = htonl(INADDR_ANY);
    
    if ( bind(lSock, (struct sockaddr *) &saddr, sizeof(saddr)) < 0 ) 
    {
       fprintf(stderr, "Bind failed\n");
       exit(EXIT_FAILURE);
    }
    
    if ( listen(lSock, 2) < 0 ) 
    {
       fprintf(stderr, "Listen failed\n");
       exit(EXIT_FAILURE);
    }
    
    if ( 1 )
    {
       if ( (dataSock = accept(lSock, NULL, NULL) ) < 0 )
       {
          fprintf(stderr, "accept failed\n");
          exit(EXIT_FAILURE);
       }
    
       processData( dataSock );
       
       if ( close(dataSock) < 0 )
       {
          fprintf(stderr, "close failed\n");
          exit(EXIT_FAILURE);
       }
    }
    
   return 0;
}


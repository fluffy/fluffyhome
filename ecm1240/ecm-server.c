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

#include <math.h>

#include <fcntl.h>
#include <sys/errno.h>

#include <termios.h>

#include <syslog.h>
#include <stdarg.h>

#include <curl/curl.h>
#include <assert.h>


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


# if 0
void
postValue( char* name , float value )
{
   fprintf(stderr,"Post %s = %f \n",name,value);

   char buf[1024];
   snprintf(buf,sizeof(buf),"curl -S --request PUT --data '%f' http://www.fluffyhome.com/sensor/fluffy/%s/value/",value,name);
   
   //fprintf(stderr,"\n%s\n\n",buf );

   int err = system( buf );
  
   if ( err != 0 )
   {
      fprintf(stderr,"System call to '%s' return value was %d\n",buf,err );
   }
}

#else

void
postValue( char* bufUrl , char* bufData )
{
   CURLcode ret;
   CURL *hnd = curl_easy_init();

   /* curl_easy_setopt(hnd, CURLOPT_WRITEDATA, 0x7fff5fbfee00); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_WRITEFUNCTION, 0x1000026f2); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_READDATA, 0x7fff5fbfee80); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_READFUNCTION, 0x100001bca); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_SEEKDATA, 0x7fff5fbfee80); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_SEEKFUNCTION, 0x100001bb4); [REMARK] */
   curl_easy_setopt(hnd, CURLOPT_INFILESIZE_LARGE, (curl_off_t)-1);
   curl_easy_setopt(hnd, CURLOPT_URL, bufUrl );
   curl_easy_setopt(hnd, CURLOPT_PROXY, NULL);

   curl_easy_setopt(hnd, CURLOPT_NOPROGRESS, 1);
   curl_easy_setopt(hnd, CURLOPT_HEADER, 0);
   curl_easy_setopt(hnd, CURLOPT_FAILONERROR, 0);
   curl_easy_setopt(hnd, CURLOPT_UPLOAD, 0);
   curl_easy_setopt(hnd, CURLOPT_NETRC, 0);
   curl_easy_setopt(hnd, CURLOPT_FOLLOWLOCATION, 0);
   curl_easy_setopt(hnd, CURLOPT_UNRESTRICTED_AUTH, 0);
   curl_easy_setopt(hnd, CURLOPT_TRANSFERTEXT, 0);
   curl_easy_setopt(hnd, CURLOPT_USERPWD, NULL);
   curl_easy_setopt(hnd, CURLOPT_PROXYUSERPWD, NULL);
   curl_easy_setopt(hnd, CURLOPT_RANGE, NULL);
   /* curl_easy_setopt(hnd, CURLOPT_ERRORBUFFER, 0x7fff5fbfefc0); [REMARK] */
   curl_easy_setopt(hnd, CURLOPT_TIMEOUT, 0);
   curl_easy_setopt(hnd, CURLOPT_POSTFIELDS, bufData );
   curl_easy_setopt(hnd, CURLOPT_POSTFIELDSIZE_LARGE, (curl_off_t)-1);
   curl_easy_setopt(hnd, CURLOPT_REFERER, NULL);
   curl_easy_setopt(hnd, CURLOPT_AUTOREFERER, 0);
   curl_easy_setopt(hnd, CURLOPT_USERAGENT, "FluffyHome ecm-server v0.01");
   curl_easy_setopt(hnd, CURLOPT_FTPPORT, NULL);
   curl_easy_setopt(hnd, CURLOPT_LOW_SPEED_LIMIT, 0);
   curl_easy_setopt(hnd, CURLOPT_LOW_SPEED_TIME, 0);
   curl_easy_setopt(hnd, CURLOPT_MAX_SEND_SPEED_LARGE, (curl_off_t)0);
   curl_easy_setopt(hnd, CURLOPT_MAX_RECV_SPEED_LARGE, (curl_off_t)0);
   curl_easy_setopt(hnd, CURLOPT_RESUME_FROM_LARGE, (curl_off_t)0);
   curl_easy_setopt(hnd, CURLOPT_COOKIE, NULL);
   curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSLCERT, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSLCERTTYPE, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSLKEY, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSLKEYTYPE, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSH_PRIVATE_KEYFILE, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSH_PUBLIC_KEYFILE, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSL_VERIFYHOST, 2);
   curl_easy_setopt(hnd, CURLOPT_MAXREDIRS, 50);
   curl_easy_setopt(hnd, CURLOPT_CRLF, 0);
   curl_easy_setopt(hnd, CURLOPT_QUOTE, NULL);
   curl_easy_setopt(hnd, CURLOPT_POSTQUOTE, NULL);
   curl_easy_setopt(hnd, CURLOPT_PREQUOTE, NULL);
   curl_easy_setopt(hnd, CURLOPT_WRITEHEADER, NULL);
   curl_easy_setopt(hnd, CURLOPT_COOKIEFILE, NULL);
   curl_easy_setopt(hnd, CURLOPT_COOKIESESSION, 0);
   curl_easy_setopt(hnd, CURLOPT_SSLVERSION, 0);
   curl_easy_setopt(hnd, CURLOPT_TIMECONDITION, 0);
   curl_easy_setopt(hnd, CURLOPT_TIMEVALUE, 0);
   curl_easy_setopt(hnd, CURLOPT_CUSTOMREQUEST, "POST");
   /* curl_easy_setopt(hnd, CURLOPT_STDERR, 0x7fff70c9e1f0); [REMARK] */
   curl_easy_setopt(hnd, CURLOPT_HTTPPROXYTUNNEL, 0);
   curl_easy_setopt(hnd, CURLOPT_INTERFACE, NULL);
   curl_easy_setopt(hnd, CURLOPT_TELNETOPTIONS, NULL);
   curl_easy_setopt(hnd, CURLOPT_RANDOM_FILE, NULL);
   curl_easy_setopt(hnd, CURLOPT_EGDSOCKET, NULL);
   curl_easy_setopt(hnd, CURLOPT_CONNECTTIMEOUT, 0);
   curl_easy_setopt(hnd, CURLOPT_ENCODING, NULL);
   curl_easy_setopt(hnd, CURLOPT_FTP_CREATE_MISSING_DIRS, 0);
   curl_easy_setopt(hnd, CURLOPT_IPRESOLVE, 0);
   curl_easy_setopt(hnd, CURLOPT_FTP_ACCOUNT, NULL);
   curl_easy_setopt(hnd, CURLOPT_IGNORE_CONTENT_LENGTH, 0);
   curl_easy_setopt(hnd, CURLOPT_FTP_SKIP_PASV_IP, 0);
   curl_easy_setopt(hnd, CURLOPT_FTP_FILEMETHOD, 0);
   curl_easy_setopt(hnd, CURLOPT_FTP_ALTERNATIVE_TO_USER, NULL);
   curl_easy_setopt(hnd, CURLOPT_SSL_SESSIONID_CACHE, 1);
   /* curl_easy_setopt(hnd, CURLOPT_SOCKOPTFUNCTION, 0x1000027ad); [REMARK] */
   /* curl_easy_setopt(hnd, CURLOPT_SOCKOPTDATA, 0x7fff5fbfea20); [REMARK] */
   ret = curl_easy_perform(hnd);
   curl_easy_cleanup(hnd);
   
   if ( (int)ret != 0 )
   {
      fprintf(stderr,"Curl call return value was %d\n", (int)ret );
   }
}


#endif



void
processValueOLD( char* sensorName,  unsigned int serial,
              float value, float* pValue, float minChange,
              int time, int* pTime, int minTimeDelta, int maxTimeDelta )
{
   assert( pValue );
   assert( pTime );
   assert( sensorName );
   
   int dTime = time - *pTime;
   if ( (dTime<=0) || (dTime>60*60) ) /* do we have a crazy time */ 
   {
      *pTime = time;
      *pValue = value;
      return;
   }

   if ( dTime < minTimeDelta)
   {
      return;
   }
   
   float dValue = value - *pValue;
   if (dValue <0.0) dValue = -dValue;
   
   if ( (dTime >= maxTimeDelta) || (dValue >= minChange) )
   {
      /* report the reading */

      char buf[1024];
      snprintf( buf , sizeof(buf), "ECM1240-%d-%s", serial, sensorName );
      //postValue( buf, value );
      
      *pValue = value;
      *pTime = time;
   }
}


void  
processPowerValueOLD( char* sensorName, 
                   int time,  unsigned int serial,
                   unsigned int wattSec, unsigned int* pWattSec, 
                   float* pWatt, int* pTime, int* pPostTime )
{
   int dTime = time - *pTime;
  
   if (dTime <= 0 )
   {
      *pWattSec = wattSec;
      *pTime = time;
      return;
   }
   
   int dWattSec = wattSec - *pWattSec;
   float watt = (float)dWattSec / (float)dTime;
   
   // fprintf(stderr,"%s watts = %f, dTime=%d wSec=%d pwSec=%d dWSec=%d\n",sensorName,watt,dTime,(int)wattSec,(int)*pWattSec,dWattSec );
   
   processValueOLD( sensorName, serial, 
                 watt, pWatt, 20.0, 
                 time, pPostTime, 5 , 60 * 10 /* randomize this a bit */ );

   *pWattSec = wattSec;
   *pTime = time;
}


typedef struct
{
      int serial;
      int time; // seconds

      int voltageX10; // volts times 10 
      int dcVoltageX100; // voltes times 100 

      int currentX100[2]; // amps times 100
      long energy[2]; // Joules
      long energyPolar[2]; // Joules

      int auxEnergy[5]; // Joules
} Value;



int abs( int x )
{
   if (x<0 )
   {
      return -x;
   }
   else
   {
      return x;
      
   }
}

   
void postMsg( char* url, Value* prev, Value* next )
{
   int i;
   
   if ( prev->time + 1 >= next->time ) return;
   
   int doPost = 0;
   
   if ( next->time > prev->time+30 ) doPost=1;
   
   if ( abs( prev->currentX100[0] - next->currentX100[0] ) >= 30 ) doPost=1;
   if ( abs( prev->currentX100[1] - next->currentX100[1] ) >= 30 ) doPost=1;
   if ( abs( prev->voltageX10 - next->voltageX10 ) >= 2 ) doPost=1;

   if (!doPost) return;
   
   char bufData[2*1024];
   int len=0;
   float value;
   len += snprintf(bufData+len,sizeof(bufData)-len,"[\n");
   
   prev->serial = next->serial;

   prev->time = next->time;
   len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-time\", \"v\":%d },\n",next->serial,next->time);

   for( i=0; i < 2 ; i++)
   {
      prev->currentX100[i] = next->currentX100[i];
      value = (float)(next->currentX100[i]) / 100.0;
      len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-current%d\", \"v\":%f },\n",next->serial,i+1,value);

      prev->energy[i] = next->energy[i];
      len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-ch%d\", \"s\":%ld },\n",next->serial,i+1,next->energy[i]);

      prev->energyPolar[i] = next->energyPolar[i];
      len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-ch%dPolar\", \"s\":%ld },\n",next->serial,i+1,next->energyPolar[i]);
   }
   for( i=0; i < 5 ; i++)
   {
      prev->auxEnergy[i] = next->auxEnergy[i];
      len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-aux%d\", \"s\":%d },\n",next->serial,i+1,next->auxEnergy[i]);
   }

   prev->voltageX10 = next->voltageX10;
   value = (float)(next->voltageX10) / 10.0;
   len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"ECM1240-%d-voltage\", \"v\":%f }\n",next->serial,value);

   len += snprintf(bufData+len,sizeof(bufData)-len,"]");

   fprintf(stderr,"Post Message len=%d to %s:\n%s\n",len,url,bufData);

   postValue( url, bufData );
   
}

   
void parseMsg( int len,  unsigned char msg[] , Value* prev, Value* next )
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
      int mOff;
      /* easiest way to sort these out is create a fake message with a bit set
      at the location in question and send it to the normal ECM software and see
      where it shows up in the output data */

      next->time = msg[35] + msg[36]*256 + msg[37]*256*256;

      next->currentX100[0] = msg[31] + msg[32]*256;
      //fprintf( stderr, "ch1amps x100 = %d \n", ch1ampsX100 );

      next->currentX100[1]  = msg[33] + msg[34]*256;
      //fprintf( stderr, "ch2amps x100 = %d \n", ch2ampsX100 );

      next->voltageX10 = msg[1]*256 + msg[2];
      //fprintf( stderr, "volts x10 = %d \n", voltsX10 );
      //float vErr = (float)(voltsX10) / 10.0 - 120.0;
      // static float pvErr = 0.0;
      // static int pvErrTime=0;
      
      next->dcVoltageX100 = msg[58] + msg[59]*256;
      //fprintf( stderr, "dcVolts x100 = %d \n", dcVoltsX100 );

      // todo relace mult with shits 
      // todo assert size long > 32 bits

      next->energy[0] = msg[3] + msg[4]*256 + msg[5]*256*256 + msg[6]*256*256*256 ; //+ msg[7]*256*256*256*256;
      //fprintf( stderr, "ch1wattSec %d \n", ch1wattSec );
      //static unsigned int pch1wattSec = 0; static float pch1watt=0.0; static int pch1time=0; static int pch1PostTime;
       
      next->energy[1] = msg[8] + msg[9]*256 + msg[10]*256*256 + msg[11]*256*256*256 ; //+ msg[12]*256*256*256*256;
      //fprintf( stderr, "ch2wattSec %d \n", ch2wattSec );
      //static unsigned int pch2wattSec = 0; static float pch2watt=0.0; static int pch2time=0; static int pch2PostTime;
     
      next->energyPolar[0] = msg[13] + msg[14]*256 + msg[15]*256*256 + msg[16]*256*256*256 ; //+ msg[17]*256*256*256*256;
      next->energyPolar[1] = msg[18] + msg[19]*256 + msg[20]*256*256 + msg[21]*256*256*256 ; //+ msg[22]*256*256*256*256;
       
      mOff = 27;
      next->serial = msg[mOff] + msg[mOff+1]*256 ;
      //fprintf( stderr, "serialNumber %d \n", serial );
 
      int i;
      for ( i=0; i<5; i++ )
      {
         mOff = 38+4*i;
         next->auxEnergy[i] = msg[mOff] + msg[mOff+1]*256 + msg[mOff+2]*256*256 + msg[mOff+3]*256*256*256;
      }
      
   
      
      //processValue(  "voltsError",  serial, vErr, &pvErr, 0.1 , seconds, &pvErrTime, 10, 60*5 );

      //processPowerValue( "ch1",  seconds, serial, ch1wattSec, &pch1wattSec, &pch1watt, &pch1time, &pch1PostTime);
      //processPowerValue( "ch2",  seconds, serial, ch2wattSec, &pch2wattSec, &pch2watt, &pch2time, &pch2PostTime);
      //processPowerValue( "aux1", seconds, serial, aux1wattSec, &paux1wattSec, &paux1watt, &paux1time, &paux1PostTime);
      //processPowerValue( "aux2", seconds, serial, aux2wattSec, &paux2wattSec, &paux2watt, &paux2time, &paux2PostTime);
      //processPowerValue( "aux3", seconds, serial, aux3wattSec, &paux3wattSec, &paux3watt, &paux3time, &paux3PostTime);
      //processPowerValue( "aux4", seconds, serial, aux4wattSec, &paux4wattSec, &paux4watt, &paux4time, &paux4PostTime);
      //processPowerValue( "aux5", seconds, serial, aux5wattSec, &paux5wattSec, &paux5watt, &paux5time, &paux5PostTime);

      //processValues( seconds, ch1wattSec, ch2wattSec, voltsX10 );
   }
}


void
processData( int sock , char* url )
{
   int c;
   
   assert( sizeof(int) >= 4 );
   assert( sizeof(long) > 4 );
   
   Value prev,next;
   prev.time = 0;
   next.time = 0;
   
   int i=0;
   
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
         parseMsg( msgPos-2 , msgBuf , &prev, &next );
         postMsg( url, &prev, &next );
      }
      else
      {
         fprintf(stderr,"Bad check sum. check=%02x sum=%02x \n",check,sum);
      }
      
   }
}


void runSerial( char* device, char* url )
{
   struct termios p;

   int fd = open(device, O_RDONLY|O_SYMLINK|O_NOCTTY  );
   if (fd == -1 )
   {
      int e = errno;
      switch (e)
      {
         case EBUSY:
            fprintf(stderr, "Device %s is already in use\n",device);
            break;
         case EACCES:
            fprintf(stderr, "Do not have permision to read device %s\n",device);
            break;
         case ENOENT:
            fprintf(stderr, "Device %s does not exist\n",device);
            break;
         default:
           fprintf(stderr, "Could not open serial device %s: errno=%d\n",device,e);
      }
      exit(EXIT_FAILURE);
   }

   int r = tcgetattr(fd,&p);
   if ( r== -1 )
   {
      int e = errno;
      fprintf(stderr, "Problem getting baud rate of device %s: errno=%d\n",device,e);
      exit(EXIT_FAILURE);
   }
   cfsetspeed(&p, B19200 );
   cfmakeraw(&p);
   r = tcsetattr(fd,TCSANOW,&p);
   if ( r== -1 )
   {
      int e = errno;
      fprintf(stderr, "Problem setting baud rate of device %s: errno=%d\n",device,e);
      exit(EXIT_FAILURE);
   }
   
  
   processData( fd , url );
}


void runIP( int port, char* url  )
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
    
       processData( dataSock, url  );
       
       if ( close(dataSock) < 0 )
       {
          fprintf(stderr, "close failed\n");
          exit(EXIT_FAILURE);
       }
    }
}


int 
main(int argc, char* argv[] )
{
   syslog(LOG_INFO,"Starting ECM 1240 Monitor");
   
   int port = 0;
   char* dev = "/dev/cu.KeySerial1";
   char* url = "http://localhost:8081/sensorValues/";
  
   if ( argc == 2 )
   {
      dev = argv[1];
      port = strtol( argv[1], NULL, 10 );
   }
   
   if ( port )
   {
      runIP( port , url );
   }
   else
   {
      runSerial( dev, url  );
   }

   return 0;
}


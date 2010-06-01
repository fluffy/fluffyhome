/* 
 * Copyright Cullen Jennings 2010. All rights reserved.
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

typedef float Value;

int verbose = 0;



unsigned char
getChar( int sock )
{
   unsigned char buf[1];

   size_t numRead = read(sock, buf, sizeof(buf) );
   
   if (numRead != sizeof(buf) )
   {
      int e = errno;
      fprintf(stderr, "error in read. Errno=%d \n",e);
      exit(EXIT_FAILURE);
   }
   //fprintf(stderr,"\nGot %d input\n",buf[0] );
   
   return buf[0];
}


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


void postMsg( char* url, char* addr, Value value1, Value value2 ) // should
                                                                  // depricate -
                                                                  // water meter uses
{
   char bufData[2*1024];
   int len=0;

   len += snprintf(bufData+len,sizeof(bufData)-len,"{\"m\":[\n");
   
   len += snprintf(bufData+len,sizeof(bufData)-len,"{\"n\":\"%s\", \"s\":%f, \"v\":%f }\n", addr, (float)value1, (float)value2 );

   len += snprintf(bufData+len,sizeof(bufData)-len,"]}");

   if ( verbose )
   {
      fprintf(stderr,"Post Message len=%d to %s:\n%s\n",len,url,bufData);
   }
   postValue( url, bufData );
}

   
int 
parseMsg( int len,  unsigned char msg[], char* url )
{
   assert( len > 1 );
   int i;
   
   char addr[100];
   

   if ( msg[0] == 0x90 )
   {
      snprintf( addr, 100 /* size */ , "ZB-%02X%02X%02X%02X%02X%02X",msg[1],msg[2],msg[3],msg[4],msg[5],msg[6] );
       
      if (0)
      {
         fprintf(stderr,"Msg: \n");
         int i;
         for ( i=0; i<len; i++ )
         {
            fprintf(stderr," %d:%02x \n",i+3,msg[i]);
         }
         fprintf(stderr,"\n");
      }
      
      assert( len > 12 );
      
      if ( verbose )
      {
         fprintf(stderr,"Msg from %s is: '%s' \n",addr,msg+12);
      }
      
      if ( len < 20 )
      {
         return 0;
      }
      
      if ( (msg[12] == 'l') && (msg[13] == ' ' ) ) // old format from old water sensor
      {
         char name[1000];    
         float val1 = 0.0;
         float val2 = 0.0;
         sscanf( msg+12, "%s %f %f", name , &val1 , &val2 );
         
         postMsg( url, addr, val1, val2 );
      }
      else if ( (msg[12] == '{') && (msg[13] == '"' ) && (msg[14] == 'm') && (msg[15] == '"') && (msg[16] == ':' ) )
      {
         char* buf = msg+12;
         if ( verbose )
         {
            fprintf(stderr,"Post Message len=%d to %s:\n%s\n",len-12,url,buf);
         }
         postValue( url, buf );
      }
      else
      {
         fprintf(stderr,"Bad message from %s is: '%s' \n",addr,msg+12);
      }
      

      return 1;
   }
   
   return 0;
}


void
processData( int sock , char* url )
{
   while (1)
   {
      unsigned char msgBuf[128];
      int i;
      unsigned char c;
      
      // find the start sync 
      do
      {
        c  = getChar( sock );
      }
      while (  c != 0x7E  ); 
         
      unsigned int msb = getChar( sock );
      unsigned int lsb = getChar( sock );

      unsigned int len = (msb << 8 ) + lsb;
      //fprintf(stderr,"len=%d \n", len );

      if ( (len<4) || (len > sizeof(msgBuf)-2 ) )
      {
         fprintf(stderr,"Message size of %d is bogus\n",len);
         continue; // go back to looking for sync, msg too large 
      }
      
      for ( i=0; i<len; i++ )
      {
         msgBuf[i] = getChar( sock );
         //fprintf(stderr," %02x",d);
      }
      msgBuf[len] = 0; // null terminate input string 
      
      unsigned char ckSum = getChar( sock );
      unsigned char cSum = 0xFF;
      for ( i=0; i<len; i++ )
      {
         cSum -= msgBuf[i];
      }
      if ( cSum != ckSum )
      {
         fprintf(stderr,"Bad check sum on message ckSum=%d cSum=%d \n",ckSum, cSum );
         continue;
      }
      
      int ok = parseMsg( len , msgBuf , url  );

      /*  if ( ok )
      {
         postMsg( url, addr, value1, value2 );
         } */
      
   }
}


int setupSerial( char* device )
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
   cfsetspeed(&p, B9600 );
   cfmakeraw(&p);
   r = tcsetattr(fd,TCSANOW,&p);
   if ( r== -1 )
   {
      int e = errno;
      fprintf(stderr, "Problem setting baud rate of device %s: errno=%d\n",device,e);
      exit(EXIT_FAILURE);
   }
   
   return fd;
}


int 
main(int argc, char* argv[] )
{
   syslog(LOG_INFO,"Starting XBEE Monitor");

   assert( sizeof(int) >= 4 );
   assert( sizeof(long long) > 4 );
   assert( sizeof(long long) <= 8 );
   
   int port = 0;
   char* dev = "/dev/cu.usbserial-FTDXSAVO";
   char* url = "http://www.fluffyhome.com/sensorValues/";
  
   if ( argc > 1 )
   {
      dev = argv[1];
   }
   
   if ( argc > 2  )
   {
      url = argv[2];
   }
   
   int sock = 0;
   
   sock = setupSerial( dev  );

   fprintf(stderr,"Starting proceessin xbee data (sock=%d) \n",sock);
   
   processData( sock , url );

   return 0;
}


/* 
 * Copyright Cullen Jennings 2009, 2010. All rights reserved.
 */

#include <unistd.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include <fcntl.h>
#include <sys/errno.h>

#include <termios.h>
#include <assert.h>


void sendMsg( int fd, unsigned char msg[], int len )
{
   int l = write( fd, msg, len );
   if ( l == -1 )
   {
      int err = errno;
      printf( "Error doing write of %s\n",strerror(err));
      exit( 1 );
   }
   assert( l == len );
}


void receiveMsg( int fd, unsigned char msg[], int* len )
{
   assert( len );
   assert( msg );
   int l;
   
   l = read( fd, msg, 2 );
   if ( l == -1 )
   {
      int err = errno;
      printf( "Error doing read of %s\n",strerror(err));
      exit( 1 );
   }
   if ( l == 0 )
   {
      printf( "Error: serial device disconnected" );
      exit( 1 );
   }
   assert( l == 2 );

   assert( msg[0] == 0x02  );
   int extraLen =-1;
   switch( msg[1] )
   {
      case 0x60: extraLen = 7; break;
      case 0x62: extraLen = 7; break;
   }
   
   l = read( fd, msg+2, extraLen );
   if ( l == -1 )
   {
      int err = errno;
      printf( "Error doing read of %s\n",strerror(err));
      exit( 1 );
   }
   if ( l == 0 )
   {
      printf( "Error: serial device disconnected" );
      exit( 1 );
   }
   assert( l == extraLen );
   
   // TODO - one more read here for extended length messages 
   *len = extraLen +2;
}


void parseMsg( int received, unsigned char msg[], int len )
{
   printf("%c: ", (char)( received?'R':'S') );
   
   int pos=0;
   if ( msg[pos] = 0x02 )
   {
      switch( msg[pos+1] )
      {
         default:
            break;
      }
   }
   
   assert( pos <= len );
   
  unkown:
   if ( len > pos )
   {
      printf("Unknown Data: ");
      int i;
      for ( i=pos; i<len; i++)
      {
         printf( " 0x%02x,",msg[i]);
      }
   }
   printf("\n");
}


void
run( int fd , char* url )
{
   int i;
   int l;
   unsigned char buf[1024]; int bufLen;
      
   assert( url );
   assert( fd != 0 );
   
   unsigned char cmd1[] = {0x02, 0x60};
   assert( sizeof(cmd1) == 2 );
   parseMsg( 0, cmd1, sizeof(cmd1) );
   sendMsg( fd, cmd1, sizeof(cmd1) );

   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );
   
   unsigned char cmd2[] = {0x02, 0x62,  0x12,0x8B,0xB0,  0x07,   0x13,0x00 }; 
   parseMsg( 0, cmd2, sizeof(cmd2) );
   sendMsg( fd, cmd2, sizeof(cmd2) );

   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );
}


int openSerial( char* device )
{
   struct termios p;

   int fd = open(device, O_RDWR|O_SYMLINK|O_NOCTTY  );
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
   
   assert( fd != 0 );
   assert( fd != -1 );
   
   return fd;
}


int 
main(int argc, char* argv[] )
{
   //syslog(LOG_INFO,"Starting ECM 1240 Monitor");
   char* dev = "/dev/cu.KeySerial1";
   char* url = "http://www.fluffyhome.com/sensorValues/";
  
   if ( argc > 1 )
   {
      dev = argv[1];
   }
   
   if ( argc > 2  )
   {
      url = argv[2];
   }
   
   int fd = openSerial( dev );
   run( fd , url  );

   return 0;
}



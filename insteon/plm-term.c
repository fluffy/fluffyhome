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


void receiveBytes( int fd, unsigned char* buf, int needed )
{
   while ( needed > 0 )
   {
      int l = read( fd, buf, needed );
      if ( l == -1 )
      {
         int err = errno;
         printf( "Error doing read of %s\n",strerror(err));
         exit( 1 );
      }
      needed -= l; buf += l;
      assert( needed >= 0 );
      if ( needed > 0 )
      {
         int e = usleep( 20*1000 /* 20 ms */ );
         assert( e == 0 );
      }
   }
}


void receiveMsg( int fd, unsigned char msg[], int* len )
{
   assert( len );
   assert( msg );
   int l;
   
   receiveBytes( fd, msg, 2 );
   
   assert( msg[0] == 0x02  );
   int totalLen =-1;
   switch( msg[1] )
   {
      case 0x50: totalLen = 11; break;
      case 0x51: totalLen = 25; break;
      case 0x52: totalLen =  4; break;
      case 0x53: totalLen = 10; break;
      case 0x54: totalLen =  3; break;
      case 0x55: totalLen =  2; break;
      case 0x56: totalLen =  7; break;
      case 0x57: totalLen = 10; break;
      case 0x58: totalLen =  3; break;
      case 0x60: totalLen =  9; break;
      case 0x61: totalLen =  6; break;
      case 0x62: totalLen =  9; break;
      case 0x63: totalLen =  5; break;
      case 0x64: totalLen =  5; break;
      case 0x65: totalLen =  3; break;
      case 0x66: totalLen =  6; break;
      case 0x67: totalLen =  3; break;
      case 0x68: totalLen =  4; break;
      case 0x69: totalLen =  3; break;
      case 0x6A: totalLen =  3; break;
      case 0x6B: totalLen =  4; break;
      case 0x6F: totalLen = 12; break;
      case 0x6c: totalLen =  3; break;
      case 0x6d: totalLen =  3; break;
      case 0x6e: totalLen =  3; break;
      case 0x70: totalLen =  4; break;
      case 0x71: totalLen =  5; break;
      case 0x72: totalLen =  3; break;
      case 0x73: totalLen =  6; break;
   }
   assert( totalLen >= 2 );
   
   receiveBytes( fd, msg+2, totalLen-2 );
      
   // TODO - one more read here for extended length messages 
   *len = totalLen;
}


int parseMsg( int received, unsigned char msg[], int len )
{
   printf("%c: ", (char)( received?'R':'S') );
   
   int pos=0;
   if ( msg[pos] = 0x02 )
   {
      switch( msg[pos+1] )
      {
         case 0x60:
         {
            printf( "Modem Info "); pos += 2;
            if (received)
            {
               printf( "addr=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
               printf( "category=%02x ",msg[pos++]);
               printf( "subcat=%02x ",msg[pos++]);
               printf( "firmware_version=%02x ",msg[pos++]);
               
               if (msg[pos] == 0x06 )
               {
                  printf("ACK \n"); pos++; return 0x60;
               }
               else
               {
                  printf("NACK(%02x)",msg[pos]); pos++;
               }
               
            }
         }
         break;


         case 0x67:
         {
            printf( "Factory Reset: "); pos += 2;
            if (received)
            {
               if (msg[pos] == 0x06 )
               {
                  printf("ACK \n"); pos++; return 0x67;
               }
               else
               {
                  printf("NACK(%02x)",msg[pos]); pos++;
               }
            }
         }
         break;

         case 0x69:
         {
            printf( "Get First Link Record: "); pos += 2;
            if (received)
            {
               if (msg[pos] == 0x06 )
               {
                  printf("ACK \n"); pos++; return 0x69;
               }
               else
               {
                  printf("NACK(%02x)",msg[pos]); pos++;
               }
               
            }
         }
         break;

         case 0x6A:
         {
            printf( "Get Next Link Record: "); pos += 2;
            if (received)
            {
               if (msg[pos] == 0x06 )
               {
                  printf("ACK \n"); pos++; return 0x6A;
               }
               else
               {
                  printf("NACK(%02x)",msg[pos]); pos++;
               }
               
            }
         }
         break;


         case 0x6F:
         {
            printf( "Manage Link "); pos += 2;
            
            printf( "controlCode=%02x ",msg[pos++]);
            printf( "linkRecordFlags=%02x ",msg[pos++]);
            printf( "group=%02x ",msg[pos++]);
            
            printf( "addr=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
            printf( "linkData=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
               
            if (received)
            {
               if (msg[pos] == 0x06 )
               {
                  printf("ACK \n"); pos++; return 0x6F;
               }
               else
               {
                  printf("NACK(%02x)",msg[pos]); pos++;
               }
               
            }
         }
         break;

         
         case 0x57:
         {
            printf( "Link record response "); pos += 2;
            
            printf( "linkRecordFlags=%02x ",msg[pos++]);
            printf( "group=%02x ",msg[pos++]);
            
            printf( "addr=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
            printf( "linkData=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;

            printf("\n"); pos++; return 0x57;
         }
         break;

 
         case 0x50:
         {
            printf( "Insteon Msg: "); pos += 2;
 
            printf( "from=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
            printf( "to=%02X:%02X:%02X ",msg[pos],msg[pos+1],msg[pos+2]); pos += 3;
           
            int flags = msg[pos++];
            int cmd1 =  msg[pos++];
            int cmd2 =  msg[pos++];

            printf( "flags=%02x ",flags);
            printf( "cmd1=%02x ",cmd1);
            printf( "cmd2=%02x ",cmd2);

            switch (cmd1)
            {
               case 0x11:
               case 0x12:
               {
                  printf( "(light on) " );
               }
               break;
               case 0x13:
               case 0x14:
               {
                  printf( "(light off) " );
               }
               break;
            }
            
            printf("\n"); pos++; return 0x50;
         }
         break;

         case 0x52:
         {
            printf( "X10 Msg: "); pos += 2;

            int house = msg[pos]>>4;
            int key = msg[pos] & 0x0F;
            pos++;
            
            if ( msg[pos] & 0x80 )
            {
               printf("House %d, command=%d \n",house,key);
            }
            else
            {
               printf("House %d, unit=%d \n",house,key);
            }
            pos++; return 0x52;
         }
         break;


         default:
            break;
      }
   }
   
   if ( pos > len )
   {
      printf( "Parse overran data pos=%d len=%d",pos,len );
   }
      
  unkown:
   if ( len > pos )
   {
      printf("Unknown Data from %d to %d: ",pos,len-1);
      int i;
      for ( i=pos; i<len; i++)
      {
         printf( " 0x%02x,",msg[i]);
      }
   }
   printf("\n");

   return 0;
}


void
run( int fd , char* url )
{
   int r;
   unsigned char buf[1024]; int bufLen;
      
   assert( url );
   assert( fd != 0 );
   
#if 1
   // get modem info 
   unsigned char cmd1[] = {0x02, 0x60};
   assert( sizeof(cmd1) == 2 );
   parseMsg( 0, cmd1, sizeof(cmd1) );
   sendMsg( fd, cmd1, sizeof(cmd1) );

   receiveMsg( fd, buf, &bufLen );
   r = parseMsg( 1, buf, bufLen );
   assert( r == 0x60 );
#endif

#if 0
   // do factory reset 
   unsigned char cmd2[] = {0x02, 0x67 };
   parseMsg( 0, cmd2, sizeof(cmd2) );
   sendMsg( fd, cmd2, sizeof(cmd2) );
   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );
#endif

#if 0
   // configure modem  into promiscous mode 
   unsigned char cmd2[] = {0x02, 0x6B, 0xD0 };
   parseMsg( 0, cmd2, sizeof(cmd2) );
   sendMsg( fd, cmd2, sizeof(cmd2) );
   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );
#endif

#if 0
   // dump all the links 
   unsigned char cmd2[] = {0x02, 0x69 };
   parseMsg( 0, cmd2, sizeof(cmd2) );
   sendMsg( fd, cmd2, sizeof(cmd2) );
   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );

   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );

   int i;
   for( i=0; i<30 ; i++ )
   {
      // read next link
      unsigned char cmd3[] = {0x02, 0x6A };
      parseMsg( 0, cmd3, sizeof(cmd2) );
      sendMsg( fd, cmd3, sizeof(cmd2) );
      receiveMsg( fd, buf, &bufLen );
      int r = parseMsg( 1, buf, bufLen );
      if ( r != 0x6a) break;
      
      receiveMsg( fd, buf, &bufLen );
      parseMsg( 1, buf, bufLen );
   }
#endif 

#if 0
   // add a link
   unsigned char cmd2[] = {0x02, 0x6F,     // add a link 
                           0x40, 0xa2, 0x01, // update, C2 DB field, group 1

                           0x13,0x1f,0x0a,  // address to add 

                           0x010,0x00,0xFF }; 
   parseMsg( 0, cmd2, sizeof(cmd2) );
   sendMsg( fd, cmd2, sizeof(cmd2) );
   receiveMsg( fd, buf, &bufLen );
   parseMsg( 1, buf, bufLen );
#endif 

#if 1
   while (1)
   {
      //listen for messages 
      receiveMsg( fd, buf, &bufLen );
      parseMsg( 1, buf, bufLen );
   }
#endif 
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



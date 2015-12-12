
#include <Adafruit_NeoPixel.h>
#define PIN 6
Adafruit_NeoPixel strip = Adafruit_NeoPixel(300, PIN, NEO_GRB + NEO_KHZ800 );


void setup() {
  strip.begin();
  strip.show();

  strip.setPixelColor(0, 255, 0, 0);
  strip.setPixelColor(1, 0, 255, 0);
  strip.setPixelColor(2, 0, 0, 255);
  strip.setPixelColor(59, 0, 255, 255);
  strip.show();

}


int a = 149;
int b = 150;
int c = 0;

void loop() {

  for ( int i = 0; i < 300; i = i + 1 )
  {
    strip.setPixelColor( i, 0, 0, 4 );
  }
  c = c + 1;
  b = b + 1;
  a = a - 1;

  if ( b >= 300 ) b = 150;
  if ( a < 0 ) a = 149;
  if ( c >= 75 ) c = 0;

  if ( c >= 0 && c < 25 ) {
    strip.setPixelColor( a,     0, 255, 0);
    strip.setPixelColor( b,     0, 255, 0);
    strip.setPixelColor( a + 1, 0, 128, 0);
    strip.setPixelColor( b - 1, 0, 128, 0);
    strip.setPixelColor( a + 2, 0, 64, 0);
    strip.setPixelColor( b - 2, 0, 64, 0);
    strip.setPixelColor( a + 3, 0, 32, 0);
    strip.setPixelColor( b - 3, 0, 32, 0);
    strip.setPixelColor( a + 4, 0, 16, 0);
    strip.setPixelColor( b - 4, 0, 16, 0);
    strip.setPixelColor( a + 5, 0, 12, 0);
    strip.setPixelColor( b - 5, 0, 12, 0);
    strip.setPixelColor( a + 6, 0, 8, 0);
    strip.setPixelColor( b - 6, 0, 8, 0);
    strip.setPixelColor( a + 7, 0, 4, 0);
    strip.setPixelColor( b - 7, 0, 4, 0);
  }

  if ( c >= 25 && c < 50 ) {
    strip.setPixelColor( a,     255, 0, 0);
    strip.setPixelColor( b,     255, 0, 0);
    strip.setPixelColor( a + 1, 128, 0, 0);
    strip.setPixelColor( b - 1, 128, 0, 0);
    strip.setPixelColor( a + 2, 64, 0, 0);
    strip.setPixelColor( b - 2, 64, 0, 0);
    strip.setPixelColor( a + 3, 32, 0, 0);
    strip.setPixelColor( b - 3, 32, 0, 0);
    strip.setPixelColor( a + 4, 16, 0, 0);
    strip.setPixelColor( b - 4, 16, 0, 0);
    strip.setPixelColor( a + 5, 12, 0, 0);
    strip.setPixelColor( b - 5, 12, 0, 0);
    strip.setPixelColor( a + 6, 8, 0, 0);
    strip.setPixelColor( b - 6, 8, 0, 0);
    strip.setPixelColor( a + 7, 4, 0, 0);
    strip.setPixelColor( b - 7, 4, 0, 0);
  }

  if ( c >= 50 && c < 75 ) {
    strip.setPixelColor( a,     255, 255, 255);
    strip.setPixelColor( b,     255, 255, 255);
    strip.setPixelColor( a + 1, 128, 128, 128);
    strip.setPixelColor( b - 1, 128, 128, 128);
    strip.setPixelColor( a + 2, 64, 64, 64);
    strip.setPixelColor( b - 2, 64, 64, 64);
    strip.setPixelColor( a + 3, 32, 32, 32);
    strip.setPixelColor( b - 3, 32, 32, 32);
    strip.setPixelColor( a + 4, 16, 16, 16);
    strip.setPixelColor( b - 4, 16, 16, 16);
    strip.setPixelColor( a + 5, 12, 12, 12);
    strip.setPixelColor( b - 5, 12, 12, 12);
    strip.setPixelColor( a + 6, 8, 8, 8);
    strip.setPixelColor( b - 6, 8, 8, 8);
    strip.setPixelColor( a + 7, 4, 4, 4);
    strip.setPixelColor( b - 7, 4, 4, 4);
  }


  strip.show();

  delay( 1 );
}

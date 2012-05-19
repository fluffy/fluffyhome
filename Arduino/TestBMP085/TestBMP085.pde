

// This code came from  http://interactive-matter.org/2009/12/arduino-barometric-pressure-sensor-bmp085/


#include <Wire.h>

#define I2C_ADDRESS 0x77 //77?

const unsigned char oversampling_setting = 0; //oversamplig for measurement
const unsigned char pressure_waittime[4] = { 
  5, 8, 14, 26 };

//just taken from the BMP085 datasheet
int ac1;
int ac2; 
int ac3; 
unsigned int ac4;
unsigned int ac5;
unsigned int ac6;
int b1; 
int b2;
int mb;
int mc;
int md;


void setup()
{  
  Serial.begin(9600);  // start serial for output
  Serial.println("Setting up BMP085");
  Wire.begin();
  bmp085_get_cal_data();
}

void bmp085_read_temperature_and_pressure(int& temperature, long& pressure);

void loop()
{
  int  temperature = 0;
  long pressure = 0;

  bmp085_read_temperature_and_pressure(&temperature,&pressure);
  Serial.print(temperature/10);
  Serial.print(".");
  Serial.print(temperature%10);
  Serial.print(" C  ");

  Serial.print(pressure/10);
  Serial.print(".");
  Serial.print(pressure%10);
  Serial.print(" hPa");

  Serial.println();
  delay(1000);
}

void bmp085_read_temperature_and_pressure(int* temperature, long* pressure) 
{
  int16_t  ut= bmp085_read_ut();
  int32_t up = bmp085_read_up();
  int32_t x1, x2, x3, b3, b5, b6, p;
  uint32_t b4, b7;

  //calculate the temperature
  x1 = ((long)ut - ac6) * ac5 >> 15;
  x2 = ((long) mc << 11) / (x1 + md);
  b5 = x1 + x2;
  *temperature = (b5 + 8) >> 4;

  //calculate the pressure
  b6 = b5 - 4000;
  x1 = (b2 * (b6 * b6 >> 12)) >> 11; 
  x2 = ac2 * b6 >> 11;
  x3 = x1 + x2;
  // b3 = (((int32_t) ac1 * 4 + x3)<<oversampling_setting + 2) >> 2; // orig

  b3 = ((((int32_t) ac1 * 4 + x3)<<oversampling_setting) + 2) >> 2; // cj modify 
  b3 = (((int32_t) ac1 * 4 + x3)<<(oversampling_setting + 2) ) >> 2; // cj modify 

  x1 = ac3 * b6 >> 13;
  x2 = (b1 * (b6 * b6 >> 12)) >> 16;
  x3 = ((x1 + x2) + 2) >> 2;
  b4 = (ac4 * (uint32_t) (x3 + 32768)) >> 15;
  b7 = ((uint32_t) up - b3) * (50000 >> oversampling_setting);
  p = b7 < 0x80000000 ? (b7 * 2) / b4 : (b7 / b4) * 2;

  x1 = (p >> 8) * (p >> 8);
  x1 = (x1 * 3038) >> 16;
  x2 = (-7357 * p) >> 16;
  *pressure = p + ((x1 + x2 + 3791) >> 4);

}


unsigned int bmp085_read_ut() 
{
  write_register(0xf4,0x2e);
  delay(5); //longer than 4.5 ms
  return read_int_register(0xf6);
}


void  bmp085_get_cal_data() 
{
  Serial.println("Reading Calibration Data");

  ac1 = read_int_register(0xAA);
  Serial.print("AC1: ");
  Serial.println(ac1,DEC);
  ac2 = read_int_register(0xAC);
  Serial.print("AC2: ");
  Serial.println(ac2,DEC);
  ac3 = read_int_register(0xAE);
  Serial.print("AC3: ");
  Serial.println(ac3,DEC);
  ac4 = read_int_register(0xB0);
  Serial.print("AC4: ");
  Serial.println(ac4,DEC);
  ac5 = read_int_register(0xB2);
  Serial.print("AC5: ");
  Serial.println(ac5,DEC);
  ac6 = read_int_register(0xB4);
  Serial.print("AC6: ");
  Serial.println(ac6,DEC);
  b1 = read_int_register(0xB6);
  Serial.print("B1: ");
  Serial.println(b1,DEC);
  b2 = read_int_register(0xB8);
  Serial.print("B2: ");
  Serial.println(b2,DEC);
  mb = read_int_register(0xBA);
  Serial.print("MB: ");
  Serial.println(mb,DEC);
  mc = read_int_register(0xBC);
  Serial.print("MC: ");
  Serial.println(mc,DEC);
  md = read_int_register(0xBE);
  Serial.print("MD: ");
  Serial.println(md,DEC);
}


long bmp085_read_up() 
{
  write_register(0xf4,0x34+(oversampling_setting<<6));
  delay(pressure_waittime[oversampling_setting]);

  unsigned char msb, lsb, xlsb;
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.send(0xf6);  // register to read
  Wire.endTransmission();

  Wire.requestFrom(I2C_ADDRESS, 3); // read a byte
  while(!Wire.available()) {
    // waiting
  }
  msb = Wire.receive();
  while(!Wire.available()) {
    // waiting
  }
  lsb |= Wire.receive();
  while(!Wire.available()) {
    // waiting
  }
  xlsb |= Wire.receive();
  return (((long)msb<<16) | ((long)lsb<<8) | ((long)xlsb)) >>(8-oversampling_setting);
}

void write_register(unsigned char r, unsigned char v)
{
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.send(r);
  Wire.send(v);
  Wire.endTransmission();
}

char read_register(unsigned char r)
{
  unsigned char v;
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.send(r);  // register to read
  Wire.endTransmission();

  Wire.requestFrom(I2C_ADDRESS, 1); // read a byte
  while(!Wire.available()) {
    // waiting
  }
  v = Wire.receive();
  return v;
}

int read_int_register(unsigned char r)
{
  unsigned char msb, lsb;
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.send(r);  // register to read
  Wire.endTransmission();

  Wire.requestFrom(I2C_ADDRESS, 2); // read a byte
  while(!Wire.available()) {
    // waiting
  }
  msb = Wire.receive();
  while(!Wire.available()) {
    // waiting
  }
  lsb = Wire.receive();
  return (((int)msb<<8) | ((int)lsb));
}





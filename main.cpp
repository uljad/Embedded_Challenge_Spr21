#include <Arduino.h>
#include <Wire.h>
#define PRESSURE_SENSOR_ADD 0x18
#define pMin 0
#define pMax 300
#define outMin 419430
#define outMax 3774874

int BAUD_RATE       = 9600;

/*==========================================
Converts pressure to real pressure
Returns a float calculated to transfer functions 
============================================*/

uint8_t readStatus(void)
{
  Wire.requestFrom(PRESSURE_SENSOR_ADD,1);
  return Wire.read();
}

float GetRealPressure (int32_t RawPressure)
{
  if (RawPressure <0)
    return (RawPressure);

  else
  {
    float psi = (RawPressure - outMin) * (pMax - pMin);
    psi /= (float)(outMax - outMin);
    psi += pMin;

    return psi;
  }
}

/*===============================
-1 = Busy
-2 = No Power
-3 = Bad Memory
-4 = Saturated
=================================*/


int32_t ReadPressure ()
{
  uint8_t status;

  Wire.beginTransmission(PRESSURE_SENSOR_ADD);
  Wire.write((uint8_t)0xAA);
  Wire.write((uint8_t)0x0);
  Wire.write((uint8_t)0x0);
  Wire.endTransmission();

  delay(9);

  Wire.requestFrom(PRESSURE_SENSOR_ADD,(uint8_t)4);

  if (Wire.available()!=0) //checking if we actually got anything back
  {        

    status=Wire.read();
    
    if (status & (1<<5)) // -- checking is bit 5 is set (=1)
    {
      return (-1); //tell us that the device is busy
      Serial.println("2");
    }

    if (!(status & (1<<6))) 
    {
      Serial.println("3");
      return (-2); //No Power
      
    }

    if (status & (1<<2)) 
    {
      Serial.println("4");
      return (-3); //Meory is bada
      
    }

    if (status & (1<<0)) 
    {
      Serial.println("5");
      return (-4); //saturated
      
    }    

    uint32_t value; // get bytes for the raw pressure value
    value = Wire.read();
    value <<= 8; //shift each time to make the int
    value |= Wire.read();
    value <<= 8;
    value |= Wire.read();

    return value;

  }

  else
    return -404; //something went very wrong

}

void setup() 
{
  Wire.begin(); 
  Serial.begin(BAUD_RATE); 
}

void loop() 
{
  int32_t RawPressure = ReadPressure();

  float myCalculatedPressure = GetRealPressure(RawPressure);

  Serial.println(myCalculatedPressure, 4); 
}
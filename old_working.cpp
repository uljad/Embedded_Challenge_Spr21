#include <Arduino.h>
#include <Wire.h>
#define PRESSURE_SENSOR_ADD 0x18
#define pMin 0
#define pMax 300
#define outMin 419430
#define outMax 3774874

/*==========================================
Converts pressure to real pressure
Returns a float calculated to transfer functions 
============================================*/

uint8_t readStatus(void)
{
  Wire.requestFrom(PRESSURE_SENSOR_ADD,1);
  return Wire.read();
}


float GetRealPressure (uint32_t RawPressure)
{
  if (RawPressure <0)
    return (RawPressure);
  else
  {
    float psi = (RawPressure - outMin) * (pMax - pMin);
    psi /= (float)(outMax - outMin);
    psi += pMin;
    // convert to desired units
    //uint32_t temp= ( ((RawPressure-(uint32_t)outMin) * ((uint32_t)pMax-(uint32_t)pMin) ) / ((uint32_t)outMax-(uint32_t)outMin) ) + (uint32_t)pMin;
    return psi;
  }
    
}

/*===============================
-1 = Busy
-2 = No Power
-3 = Bad Memory
-4 = Saturated
=================================*/


uint32_t ReadPressure ()
{

  uint8_t status;

  //3 bytes for pressure data
  uint32_t pByte0;
  uint32_t pByte1;
  uint32_t pByte2;
  uint32_t mypressure[4];
  int UseCasting=0;

  Wire.beginTransmission(PRESSURE_SENSOR_ADD);
  Wire.write((uint8_t)0xAA);
  Wire.write((uint8_t)0x0);
  Wire.write((uint8_t)0x0);
  Wire.endTransmission();

  //status=readStatus();

  //

  delay(20);
  Wire.requestFrom(PRESSURE_SENSOR_ADD,(uint8_t)4);

  if (Wire.available()!=0) //checking if we actually got anything back
  {        
    //Serial.println("1");
    //Serial.println("1y");
    status=Wire.read();
    //while(readStatus() & (1<<5));
    delay(50);
    //Serial.print("status: ");
    //Serial.println(status,HEX );
  
    // pByte0 = Wire.read();
    // pByte1 = Wire.read();
    // pByte2 = Wire.read();
    // Serial.print("pByte0: ");
    // Serial.println(pByte0, BIN);
    // Serial.print("pByte0: ");
    // Serial.println(pByte1, BIN);
    // Serial.print("pByte0: ");
    // Serial.println(pByte2, BIN);

    //Serial.println("read_full");
    // uint32_t a = 0;
    // uint32_t temp = a +  (uint32_t)pByte2 + (((uint32_t)pByte1)<<8) + (((uint32_t)pByte2)<<16) ;

    uint32_t ret;
    ret = Wire.read();
    ret <<= 8;
    ret |= Wire.read();
    ret <<= 8;
    ret |= Wire.read();

    //Serial.print("temp: ");
   // Serial.println(ret, BIN);
    return ret;

    // if (status & (1<<5)) //checking is bit 5 is set (=1)
    // {
    //   return (-1); //tell us that the device is busy
    //   Serial.println("2");
    // }

    // if (!(status & (1<<6))) 
    // {
    //   Serial.println("3");
    //   return (-2); //No Power
      
    // }

    // if (status & (1<<2)) 
    // {
    //   Serial.println("4");
    //   return (-3); //Meory is bada
      
    // }

    // if (status & (1<<0)) 
    // {
    //   Serial.println("5");
    //   return (-4); //saturated
      
    // }

    // if (!UseCasting)
    // {
    //   pByte0 = Wire.read();
    //   pByte1 = Wire.read();
    //   pByte2 = Wire.read();
    //   Serial.println("read_full");
    //   return ( (uint32_t)pByte0 + (((uint32_t)pByte1)<<8) + (((uint32_t)pByte2)<<16)); //after the second lecture fixing to make sure we are not shifting beyond
    // }

    // else
    // {
    //   Serial.println("7");
    //   mypressure[3]=0;
    //   mypressure[2]=Wire.read();
    //   mypressure[1]=Wire.read();
    //   mypressure[0]=Wire.read();
    //   Serial.println("7");
    //   return ((uint32_t)mypressure);
    // }

  }


//  Serial.println("Finally");
//   return 404;

}


void setup() {

  Wire.begin(); 
  Serial.begin(9600);
  

  //Serial.println("starting");


  
}

void loop() {

  
  uint32_t RawPressure = ReadPressure();
  // Serial.print("RawPressure (BIN): ");
  // Serial.println(RawPressure, BIN);
  // Serial.print("RawPressure (DEC): ");
  // Serial.println(RawPressure, DEC);

  uint32_t myCalculatedPressure = GetRealPressure(RawPressure);
  // Serial.print("myCalculatedPressure (BIN): ");
  // Serial.println(myCalculatedPressure, BIN);
  // Serial.print("myCalculatedPressure (DEC): ");
  // Serial.println(myCalculatedPressure, DEC);



  // Serial.println("In Loop");

  if (myCalculatedPressure<0)
  {
    //Life is tough
    Serial.println("Life is tough");
    switch (myCalculatedPressure)
    {
    case -1:
      Serial.println("case -1");
      break;

    case -2: 
      Serial.println("case -2");
      break;

    case -3:
      Serial.println("case -3");
      break;
    
    case -4:
      Serial.println("case -4");
      break;
    default:
      Serial.print("something is wrong: ");
    }
  }
  
  else 
  {
    //Serial.println("good");
    Serial.println(myCalculatedPressure);
  }


  delay(10);
}
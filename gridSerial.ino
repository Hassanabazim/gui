
#include <SPI.h>

// const byte b1 = 11;
// const byte b2 = 10;
// const byte b3 = 12;

const int blocks = 5*8*2; 
const int blocksHalf = blocks / 2;
//const int lines = 2;
const int bits = blocks * 8;

const bool forward = false;
const unsigned int maxTime = -1;

// int pos = -1;
bool dir = true;
bool prevLeft = false, prevRight = false;

//Pin connected to ST_CP of 74HC595
#if DOUBLE_LATCH
int latchPin1 = 3;
int latchPin2 = 8;
int outputEnablePin = 4;
#else
int latchPin1 = A1;
int outputEnablePin = A2;
#endif

const int hallCount = 2;
int hallPins[hallCount] = {A5, A4};
int hallReference[hallCount];
int hallDiff[hallCount];

//Pin connected to SH_CP of 74HC595
//int clockPin = 2;
////Pin connected to DS of 74HC595
//int dataPin = 5;

//int dataPin2 = 10;

const int maxElements = 100;
int totalElements = 0;

bool isMoving = false;

struct Element {
  int index;
  int delay;
  unsigned int duration;
  // char is unsigned byte
  char hallBlock;
};

Element elements[maxElements];

byte writes[blocks];

unsigned long prevMillis = 0;

void clearAndWrite() {
  clear();
  writeCur();
}

void clear() {
  totalElements = 0;
  for (int i = 0; i < blocks; i++) {
    writes[i] = 0;
  }
}

void setup() {
  // pinMode(b1, INPUT_PULLUP);
  // pinMode(b2, INPUT_PULLUP);
  // pinMode(b3, INPUT_PULLUP);

  SPI.begin();

  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(latchPin1, OUTPUT);
#if DOUBLE_LATCH
  pinMode(latchPin2, OUTPUT);
#endif
  pinMode(outputEnablePin, OUTPUT);
  for (int i = 0; i < hallCount; i++) {
    pinMode(hallPins[i], INPUT);
  }

//  pinMode(clockPin, OUTPUT);
//  pinMode(dataPin, OUTPUT);
//  pinMode(dataPin2, OUTPUT);

  digitalWrite(outputEnablePin, 1);
  clearAndWrite();
  digitalWrite(outputEnablePin, 0);
  
  Serial.begin(115200);
  Serial.println("start");
  Serial.setTimeout(10);

  delay(1000);
  
  for (int i = 0; i < hallCount; i++) {
    hallReference[i] = analogRead(hallPins[i]);
  }
}

bool pressed(byte pin) {
  return !digitalRead(pin);
}

unsigned long lastLoop = 0;

void loop() {
//  unsigned long diff2 = micros() - lastLoop;
//  Serial.println(diff2);
//  lastLoop = micros();
  
  // bool enabled = pressed(b1);
  // bool left = pressed(b2);
  // bool right = pressed(b3);

  //writes[0][0] = 1;

//  for (int i = 0; i < hallCount; i++) {
//    hallDiff[i] = analogRead(hallPins[i]) - hallReference[i];
//    if (abs(hallDiff[i]) > 3) {
//      Serial.print("hall ");
//      Serial.print(i);
//      Serial.print(':');
//      Serial.println(hallDiff[i]);
//    }
//  }

a 3 30 0 350 71 0 30 32 0 30
  
  if (Serial.available() > 0) {
    char val = Serial.read();
    if (val == 'a') {
      clear();
      unsigned long curMillis = millis();
      int cnt = Serial.parseInt(); // index of the block 
      int currentElement = 0;
      for (int i = 0; i < cnt; i++) {
        int cur = Serial.parseInt();    // bit number resepective to (8 * blocks = 640 ) no.of coil 
        elements[currentElement].index = cur;
        elements[currentElement].hallBlock = -1; // hall effect sensor
        int duration1 = Serial.parseInt(); // delay
        if (duration1 >= 0) {
          int duration2 = Serial.parseInt(); // duration 
          elements[currentElement].delay = duration1;
          elements[currentElement].duration = duration2;
        }
        else {
          elements[currentElement].delay = 0;
          elements[currentElement].duration = maxTime;
        }
        if (cur >= 0 && cur < bits) {
          currentElement++;
        }
      }
      totalElements = currentElement;
      isMoving = totalElements > 0;
      digitalWrite(LED_BUILTIN, cnt > 0);
    }
    else if (val == 'A') {
      Serial.println('A');
    }
  }

  unsigned long curMillis = millis();
  unsigned long diff = curMillis - prevMillis;
  prevMillis = curMillis;

  for (int i = 0; i < blocks; i++) {
    writes[i] = 0;
  }
  bool isMovingNow = false;
  for (int i = 0; i < totalElements; i++) {
    if (elements[i].hallBlock != -1) {
      
      //Serial.print(i); Serial.print(' ');
      //Serial.print(elements[i].hallBlock); Serial.println();
      
      byte hallIdx = elements[i].hallBlock;
      if (hallDiff[hallIdx] > 20) {
        elements[i].hallBlock = -1;
        for (int j = 0; j < i; j++) {
          elements[j].duration = 0;
        }
      } else {
        isMovingNow = true;
        break;
      }
    }
    if (elements[i].delay > 0) {
      isMovingNow = true;
      if (elements[i].delay >= diff) {
        elements[i].delay -= diff;
      } else {
        unsigned long left = diff - elements[i].delay;
        elements[i].delay = 0;
      }
    } else {
      if (elements[i].duration != maxTime) {
        if (elements[i].duration >= diff) {
          elements[i].duration -= diff;
        } else {
          elements[i].duration = 0;
        }
      }
    }
    if (elements[i].delay == 0 && elements[i].duration > 0) {
      isMovingNow = true;
      int idx = elements[i].index;
      int block = idx / 8;
      writes[block] |= 1 << (idx % 8);
    }
  }
  if (!isMovingNow && isMoving) {
    isMoving = false;
    Serial.println('F');
  }

  writeCur();

  delay(1);
}

// void wtiteEnable(byte pin, bool value, bool enableValue, int pwm) {
//   analogWrite(pin, enableValue ? (value ? pwm : 0) : (value ? (255 - pwm) : 255));
//   //digitalWrite(pin, enableValue ? value : !value);
// }

void writeCur() {
  shiftOut();
}

// void writeB(byte data1, byte data2) {
//   digitalWrite(latchPin, 0);
//   shiftOut(dataPin, clockPin, data1);
//   shiftOut(dataPin, clockPin, data2);
//   digitalWrite(latchPin, 1);
// }

void shiftOut() {
//  digitalWrite(dataPin1, 0);
//  digitalWrite(dataPin2, 0);
//  digitalWrite(myClockPin, 0);
  //for each bit in the byte myDataOut&#xFFFD;
  //NOTICE THAT WE ARE COUNTING DOWN in our for loop
  //This means that %00000001 or "1" will go through such
  //that it will be pin Q0 that lights.

  //bool enable = curMillis % 2 == 0;
  
//  for (int i = bits - 1; i >= 0; i--) {
//    digitalWrite(myClockPin, 0);
//    //if the value passed to myDataOut and a bitmask result
//    // true then... so if we are at i=6 and our value is
//    // %11010100 it would the code compares it to %01000000
//    // and proceeds to set pinState to 1.
//    int idx = i / 8;
//    int shift = i % 8;
//    digitalWrite(dataPin1, (writes[0][idx] >> shift) & 1);
//    digitalWrite(dataPin2, (writes[1][idx] >> shift) & 1);
//
////    digitalWrite(dataPin1, 0);
////    digitalWrite(dataPin2, 0);
//    
//    digitalWrite(myClockPin, 1);
////    digitalWrite(dataPin1, 0);
////    digitalWrite(dataPin2, 0);
//  }

#if DOUBLE_LATCH
  digitalWrite(latchPin2, 0);
  for (int i = blocks - 1; i >= blocksHalf; i--) {
    SPI.transfer(writes[i]);
  }
  digitalWrite(latchPin2, 1);
#endif

  digitalWrite(latchPin1, 0);
  for (int i = blocksHalf - 1; i >= 0; i--) {
    SPI.transfer(writes[i]);
  }
  digitalWrite(latchPin1, 1);
  
//  digitalWrite(myClockPin, 0);
}

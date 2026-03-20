#include <Arduino.h>
#include <AccelStepper.h>

// Pin Assignments
const uint8_t STEP_PIN = 27;
const uint8_t DIR_PIN = 14;
//const uint8_t ENA_PIN = 21;

// Params
const float ACCELERATION = 32000.0;

// Driver
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// Serial Line Buffer
String inputBuffer = "";
bool wasMoving = false;

void processCommand(const String &cmd);

// Setup
void setup() {
  Serial.begin(115200);

  //pinMode(ENA_PIN, OUTPUT);     // Always on, so floating
  //digitalWrite(ENA_PIN, LOW);

  stepper.setMaxSpeed(500000.0);
  stepper.setAcceleration(ACCELERATION);

  Serial.println("READY");
}

// Loop
void loop() {
  stepper.run();

  while (Serial.available()){         
    char c = (char)Serial.read();     
    if (c == '\n' || c == '\r') {     
      if (inputBuffer.length() > 0) { 
        processCommand(inputBuffer);  
        inputBuffer = "";             
      }
    } else {
      inputBuffer += c;               
    }
  }

  bool isMoving = (stepper.distanceToGo() != 0);    
  if (wasMoving && !isMoving) {                     
    Serial.println("DONE");
  }
  wasMoving = isMoving;                             
}

// Process Command
void processCommand(const String &cmd) {
  if (cmd.startsWith("MOVE ")) {
    long steps;
    float stepsPerSec;
    if (sscanf(cmd.c_str(), "MOVE %ld %f", &steps, &stepsPerSec) == 2) {
      stepper.setMaxSpeed(max(stepsPerSec, 1.0f));
      stepper.move(steps);
    } else {
      Serial.println("ERROR bad MOVE syntax");
    }
  } else if (cmd == "STOP") {
    stepper.stop();
    Serial.println("STOPPED");
  } else if (cmd == "STATUS") {
    Serial.println(stepper.distanceToGo() != 0 ? "MOVING" : "IDLE");
  } else if (cmd == "ZERO") {
    stepper.setCurrentPosition(0);
    Serial.println("ZEROED");
  } else if (cmd == "PING") {
    Serial.println("READY");
  } else {
    Serial.print("ERROR unknown command: ");
    Serial.println(cmd);
  }
}
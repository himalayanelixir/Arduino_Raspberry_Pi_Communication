// Copyright 2020 Harlen Bains
// Linted using cpplint
// Google C++ Style Guide https://google.github.io/styleguide/cppguide.html
#include <Servo.h>
#include <String.h>

// constants
#define ARRAY_NUMBER 1
#define MESSAGE_CHAR_LENGTH 300

// function declarations
void RecvWithStartEndMarkers();
void Finished();
void PopulateArray();
String GetValue();
void ProcessData();
int CountMoving();
void CheckCounter();
void StartMotors();
int CheckSwitch();
void StartMotors();

// variables for communication
char received_chars[MESSAGE_CHAR_LENGTH];
bool new_data = false;

// integer array that contains the direction and number of rotations a motor,
// and a flag that determines if it's moving, and another number that determines
// if we are ignoreing inputs from the switches or not
int motor_commands[NUMBER_OF_MOTORS][4] = { 0 };
// other variables needed for the ProcessData() function
bool go = true;

void setup() {
  // setup serial port
  Serial.begin(9600);
  // initialize led
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  // send ready message to Raspberry Pi
  Serial.print("<");
  Serial.print("Arduino is ready");
  Serial.print(" Array Number: ");
  Serial.print(ARRAY_NUMBER);
  Serial.print(">");
}

void loop() {
  // check to see if there is any new data
  RecvWithStartEndMarkers();
  // if there is new data process it
  if (new_data == true) {
    new_data = false;
    go = true;
    did_timeout = false;
    timeout_counter = 0;
    Serial.print("<");
    PopulateArray();
    ProcessData();
    Finished();
  }
}

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

void RecvWithStartEndMarkers() {
  // handles the receiving of data over the serial port
  static bool receive_in_progress = false;
  static int char_count = 0;
  char start_marker = '<';
  char end_marker = '>';
  char receive_from_usb;
  while (Serial.available() > 0 && new_data == false) {
    receive_from_usb = Serial.read();
    if (receive_in_progress == true) {
      if (receive_from_usb != end_marker) {
        received_chars[char_count] = receive_from_usb;
        char_count++;
        if (char_count >= MESSAGE_CHAR_LENGTH) {
          char_count = MESSAGE_CHAR_LENGTH - 1;
        }
      } else {
        received_chars[char_count] = '\0';  // terminate the string
        receive_in_progress = false;
        char_count = 0;
        new_data = true;
      }
    } else if (receive_from_usb == start_marker) {
      receive_in_progress = true;
    }
  }
}

void Finished() {
  // sends message back to raspberry pi saying the command has been executed
  Serial.print("\033[32m");
  Serial.print("RECIEVED: DONE");
  Serial.print("\033[0m");
  Serial.print(">");
}

void PopulateArray() {
  // fills array with instructions from the raspberry pi
  // temp string used to store the char array
  // easier to do opperations on string than chars
  String received_string = "";
  // give the string the value of the char array
  received_string = received_chars;

  // now lets populate the motor command array with values from the received
  // string
  for (int i = 0; i < NUMBER_OF_MOTORS; i++) {
    // we break everything in to pairs of values
    int search_1 = (i *2);
    int search_2 = ((i *2) + 1);

    String value_1 = GetValue(received_string, ',', search_1);
    String value_2 = GetValue(received_string, ',', search_2);

    if (value_1 == "Up") {
      motor_commands[i][0] = 1;
    } else if (value_1 == "Down") {
      motor_commands[i][0] = 2;
    } else if (value_1 == "None") {
      motor_commands[i][0] = 0;
    } else if (value_1 == "Reset") {
      motor_commands[i][0] = 3;
    } else {
      // Sends Error Message
    }

    motor_commands[i][1] = value_2.toInt();
  }
}

String GetValue(String data, char separator, int index) {
  // helps get a particular value from the incoming data string
  int found = 0;
  int string_index[] = { 0, -1 };
  int maximum_index = data.length() - 1;

  for (int i = 0; i <= maximum_index && found <= index; i++) {
    if (data.charAt(i) == separator || i == maximum_index) {
      found++;
      string_index[0] = string_index[1] + 1;
      string_index[1] = (i == maximum_index) ? i + 1 : i;
    }
  }
  return found > index ? data.substring(string_index[0], string_index[1]) : "";
}

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

void ProcessData() {
  // function that moves the motors and executes till they are done moving or
  // timeout
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on 
    delay(1000);                       // wait for half a second
    digitalWrite(LED_BUILTIN, LOW); 
    delay(1000);
  }   
}
// Copyright 2020 Harlen Bains
// Linted using cpplint
// Formatted clang-format
// Google C++ Style Guide https://google.github.io/styleguide/cppguide.html
#include <Servo.h>
#include <String.h>

// constants
#define IGNORE_INPUT_TIME 150
#define MESSAGE_CHAR_LENGTH 300
#define START_MARKER '<'
#define END_MARKER '>'
// function declarations
void RecvWithStartEndMarkers();
void Finished();
void ProcessData();

// variables for communication
char received_chars[MESSAGE_CHAR_LENGTH];
bool new_data = false;
// number of times we want the LED to blink
int number_of_blinks = 0;

void setup() {
  // setup serial port
  Serial.begin(9600);
  // initialize built in LED port
  pinMode(LED_BUILTIN, OUTPUT);
  // send message to Raspberry Pi
  Serial.print("<");
  Serial.print("LED Port: ");
  Serial.print(LED_BUILTIN);
  Serial.print(" Arduino is ready");
  Serial.print(">");
}

void loop() {
  // check to see if there is any new data
  RecvWithStartEndMarkers();
  // if there is new data process it
  if (new_data == true) {
    new_data = false;
    Serial.print("<");
    ProcessData();
    Finished();
  }
}

void RecvWithStartEndMarkers() {
  // handles the receiving of data over the serial port
  static bool receive_in_progress = false;
  static int char_count = 0;
  char receive_from_usb;
  while (Serial.available() > 0 && new_data == false) {
    receive_from_usb = Serial.read();
    if (receive_in_progress == true) {
      if (receive_from_usb != END_MARKER) {
        received_chars[char_count] = receive_from_usb;
        char_count++;
        if (char_count >= MESSAGE_CHAR_LENGTH) {
          char_count = MESSAGE_CHAR_LENGTH - 1;
        }
      } else {
        received_chars[char_count] = '\0'; // terminate the string
        receive_in_progress = false;
        char_count = 0;
        new_data = true;
      }
    } else if (receive_from_usb == START_MARKER) {
      receive_in_progress = true;
    }
  }
}

void Finished() {
  // sends message back to raspberry pi saying the command has been executed
  Serial.print("\033[32m");
  Serial.print("DONE ");
  Serial.print(number_of_blinks);
  Serial.print("\033[0m");
  Serial.print(">");
}

void ProcessData() {
  number_of_blinks = atoi(received_chars);
  for (int i = 0; i < number_of_blinks; i++) {
    digitalWrite(LED_BUILTIN, HIGH); // turn the LED on
    delay(1000);                     // wait for a second
    digitalWrite(LED_BUILTIN, LOW);  // turn the LED off
    delay(1000);                     // wait for a second
  }
}

#include <Servo.h>
#include <String.h>

// constants
#define DEBOUNCE_TIME .5
#define SAMPLE_FREQUENCY 20
#define MAXIMUM (DEBOUNCE_TIME * SAMPLE_FREQUENCY)
#define NUMBER_MOTORS 2

// function declarations
void RecvWithStartEndMarkers();
void ProcessData();
void ShowNewData();

// variables for communication
const byte numChars = 32;
char receivedChars[numChars];
bool newData = false;


void setup()
{
  // setup serial port
  Serial.begin(9600);


  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.println("");
  Serial.println("<");
  Serial.println("Arduino is ready");
  Serial.println(">");
}

void loop()
{
  // check to see if there is any new data
  RecvWithStartEndMarkers();

  // if there is new data process it
  if (newData == true)
  {
    newData = false;
    Serial.println("<");
    Serial.print("Arduino: ");
    Serial.println(receivedChars);
    ProcessData();
  }
}
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Set the LCD address to 0x27 for a 20 chars and 4 line display
// Change the address if your I2C scanner says otherwise
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Backlight PWM pin (Optional hardware mod: connect I2C jumper pin to D9)
const int BACKLIGHT_PIN = 9; 
const int BUTTON_PIN = 2; // Button pin for view cycling

bool usePWM = false;
bool lastReading = HIGH;
bool lastStableState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

void setup() {
  Serial.begin(115200);
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  lcd.init();
  lcd.backlight();
  
  pinMode(BACKLIGHT_PIN, OUTPUT); 
  usePWM = true;
  analogWrite(BACKLIGHT_PIN, 255);

  lcd.setCursor(0, 0);
  lcd.print("Plex Monitor v3.2");
  lcd.setCursor(0, 1);
  lcd.print("Button Fixed (D2)");
  lcd.setCursor(0, 2);
  lcd.print("Baud Rate: 115200");
  lcd.setCursor(0, 3);
  lcd.print("Waiting for data...");
}

char textBuffer[81];

void loop() {
  // --- Handle Button Press (Improved Debounce) ---
  bool reading = digitalRead(BUTTON_PIN);
  if (reading != lastReading) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (reading != lastStableState) {
      lastStableState = reading;
      if (lastStableState == LOW) {
        Serial.print('N'); // Send 'Next View' signal
      }
    }
  }
  lastReading = reading;

  // --- Handle Serial Data ---
  if (Serial.available() > 0) {
    // Look for the start marker '!'
    if (Serial.read() == '!') {
      int count = 0;
      uint8_t brightness = 255;
      unsigned long startTime = millis();
      
      while (count < 81 && (millis() - startTime < 200)) {
        if (Serial.available() > 0) {
          if (count < 80) {
            textBuffer[count] = Serial.read();
          } else {
            brightness = Serial.read();
          }
          count++;
        }
      }

      if (count == 81) {
        if (usePWM) {
          analogWrite(BACKLIGHT_PIN, brightness);
        } else {
          if (brightness > 0) lcd.backlight();
          else lcd.noBacklight();
        }
        
        for (int line = 0; line < 4; line++) {
          lcd.setCursor(0, line);
          for (int col = 0; col < 20; col++) {
            lcd.print(textBuffer[line * 20 + col]);
          }
        }
      }
    }
  }
}

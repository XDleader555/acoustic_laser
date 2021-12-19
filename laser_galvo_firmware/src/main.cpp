/**
 * main.cpp - Laser Galvo Firmware
 * Copyright (c) 2021 Andrew Miyaguchi [https://github.com/XDleader555/acoustic_laser]
 *
 * The mirror of the laser is 24 mm from the front of the device
 * Test grid is Y328.8 mm
 * Test fixture is 342.9 mm + 80.7 mm + 24 mm = X0 Y447.6 Z56
 * 
 * References
 * https://arduinoinfo.mywikis.net/wiki/Arduino-PWM-Frequency
 * 
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include "lasergalvo.h"
#include "configuration.h"
//#include "avr8-stub.h"

MiyaSh sh;

Adafruit_MCP4725 dacx;
Adafruit_MCP4725 dacz;
LaserGalvo galvo([](uint16_t output){dacx.setVoltage(output, false);},
                 false, // Invert Axis
                 [](uint16_t output){dacz.setVoltage(output, false);},
                 true); // Invert Axis

long pot_wd = 0;
long dac_wd = 0;
bool laser = false;
char linebuf[64];
uint16_t pot_read = 0;

#define SINE_SZ 32
uint16_t sine[] = {2048, 2448, 2832, 3186, 3496, 3751, 3940, 4057, 4095, 4057, 3940, 3751, 3496, 3186, 2832, 2448, 2048, 1648, 1264, 910, 600, 345, 156, 39, 0, 39, 156, 345, 600, 910, 1264, 1648};
uint16_t dacx_idx = 0;
uint16_t dacz_idx = 7;

long temp_wd = 0;
int16_t temp_raw = 0;
float temp_celsius = 0;

void setup() {
  //debug_init();
  Serial.begin(115200);
  while(!Serial);
  Serial.println("Connected");

  // For Adafruit MCP4725A1 the address is 0x62 (default) or 0x63 (ADDR pin tied to VCC)
  // For MCP4725A0 the address is 0x60 or 0x61
  // For MCP4725A2 the address is 0x64 or 0x65
  Serial.print("Connecting to DAC Y...");
  if(!dacz.begin(DAC_Y_ADDR)) {
    Serial.println("fail\n");
    while(1);
  }
  Serial.println("success");

  Serial.print("Connecting to DAC X...");
  if(!dacx.begin(DAC_X_ADDR)) {
    Serial.println("fail\n");
    while(1);
  }
  Serial.println("success");
  Serial.println("DACs Connected");

  // Set PWM frequency for D9 & D10 to something outside our hearing range
  TCCR1B = ((TCCR1B & B11111000) | B00000001);    // set timer 1 divisor to     1 for PWM frequency of 31372.55 Hz

  // Setup outputs
  pinMode(LASER_PIN, OUTPUT);
  pinMode(CASE_FAN_PIN, OUTPUT);
  pinMode(GALVO_FAN_PIN, OUTPUT);
  //pinMode(A0, INPUT); // Debug Potentiometer
  //pinMode(A1, INPUT); // EPCOS 100K Thermistor

  // Enable galvo driver cooling.
  analogWrite(GALVO_FAN_PIN, 254);
  analogWrite(CASE_FAN_PIN, 210);

  // Register commands
  sh.registerCmd("G1", "G-code", G1); // Linear Move
  sh.registerCmd("M3", "G-code", M3); // Laser Enable
  sh.registerCmd("M5", "G-code", M5); // Laser Disable
  //sh.registerCmd("M105", "G-code", M105); // Report Temperatures

  sh.begin();
}

void loop() {
  sh.run();
}

/**
 * gcode.h - Laser Galvo Firmware
 * Copyright (c) 2021 Andrew Miyaguchi [https://github.com/XDleader555/acoustic_laser]
 *
 * Gcode routines based on grbl
 * Copyright (c) 2021 Sungeun K. Jeon [https://github.com/grbl/grbl]
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

#pragma once

#include "lasergalvo.h"
#include "configuration.h"

extern char linebuf[];
extern LaserGalvo galvo;
extern float analog_to_celsius_galvo(const int raw);

// G1 - Linear Move
inline void G1(MiyaSh* shell, char* args[], int arglen) {
  int i;
  double x, y, z;
  char* arg;

  if(arglen == 0 || !strcmp(args[0], "-h")) {
    Serial.print(F("G1 - Linear Move\r\nUsage: G1 X10 Y10 Z10\r\n\r\nA linear move traces a straight line from one point to another.\r\n"));
    return;
  }

  if(arglen > 0) {

    for(i = 0; i < arglen; i ++) {
      arg = args[i];
      if(arg[0]  == 'X') {
        arg++;
        x = atof(arg);
      } else if(arg[0]  == 'Y') {
        arg++;
        y = atof(arg);
      } else if(arg[0]  == 'Z') {
        arg++;
        z = atof(arg);
      }
    }

    if(x+y+z == 0) {
        return;
    }

    // debug
    //sprintf(linebuf, "x:%.2f, y:%.2f, z:%.2f\n", x, y, z);
    //Serial.print(linebuf);

    galvo.setPos(x, y, z);
  }

  // don't reply otherwise
}

// M3 - Laser Enable
inline void M3(MiyaSh* shell, char* args[], int arglen) {
  digitalWrite(LASER_PIN, HIGH);
  Serial.println("Laser Enabled");
}

// M5 - Laser Disable
inline void M5(MiyaSh* shell, char* args[], int arglen) {
  digitalWrite(LASER_PIN, LOW);
  Serial.println("Laser Disabled");
}

// M105 - Report Temperatures
inline void M105(MiyaSh* shell, char* args[], int arglen) {
  float tempc;

  // Since there's only one thermistor, just ignore arguments
  tempc = analog_to_celsius_galvo(analogRead(A1));
  sprintf(linebuf, "Driver: %.2f°C\n", (double) tempc);
  Serial.print(linebuf);
}

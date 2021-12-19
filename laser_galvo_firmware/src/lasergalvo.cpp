/**
 * lasergalvo.cpp - Laser Galvo Firmware
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

#include "lasergalvo.h"

LaserGalvo::LaserGalvo(void (*setVoltageXCallback)(uint16_t output),
                       bool xinverted,
                       void (*setVoltageZCallback)(uint16_t output),
                       bool zinverted) {
    this->setVoltageX = setVoltageXCallback;
    this->setVoltageZ = setVoltageZCallback;
    this->xinverted = xinverted;
    this->zinverted = zinverted;
}

extern char linebuf[64];

void LaserGalvo::setPos(double x, double y, double z) {
    double voltZ;
    double voltX;
    // Z is up and down, X is left and right. All calculations are in radians
    zAxis = atan(z/y);
    xAxis = atan(x/(H1 + sqrt(y*y + z * z)));

    // Bound the positions
    zAxis = min(max(zAxis, -ANGLE_MAX), ANGLE_MAX);
    xAxis = min(max(xAxis, -ANGLE_MAX), ANGLE_MAX);

    sprintf(linebuf, "x: %.2f, y: %.2f, z: %.2f, xAxis: %.2frad, zAxis: %.2frad\n", x, y, z, xAxis, zAxis);
    Serial.println(linebuf);

    // PI/9 is 20 degrees
    if(zinverted) {
        voltZ = mapf(zAxis, -ANGLE_MAX, ANGLE_MAX, 4095, 0);
    } else {
        voltZ = mapf(zAxis, -ANGLE_MAX, ANGLE_MAX, 0, 4095);
    }
    
    if(xinverted) {
        voltX = mapf(xAxis, -ANGLE_MAX, ANGLE_MAX, 4095, 0);
    } else {
        voltX = mapf(xAxis, -ANGLE_MAX, ANGLE_MAX, 0, 4095);
    }

    (*setVoltageZ)(voltZ);
    (*setVoltageX)(voltX);
}
/**
 * lasergalvo.h - Laser Galvo Firmware
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

/**
 * About LaserGalvo
 * 
 * This firmware takes gcode commands and processes for use with a laser
 * galvonometer.
 * 
 * All distances are in centimeters
 */

#pragma once

// Standard libraries
#include <stdint.h>
#include <stdbool.h>

// Third party libraries
#include <Adafruit_MCP4725.h>

// Project libraries
#include "mapf.h"
#include <MiyaSh.h>
#include "temperature.h"

// distance from xAxis to zAxis
#define H1 (0.85)
#define ANGLE_MAX PI/9

class LaserGalvo {
private:
    double xAxis;
    double zAxis;
    void (*setVoltageX)(uint16_t output);
    void (*setVoltageZ)(uint16_t output);
    bool xinverted;
    bool zinverted;

public:
    LaserGalvo(void (*setVoltageX)(uint16_t output),
               bool xinverted,
               void (*setVoltageZ)(uint16_t output),
               bool zinverted);

    /**
     * Set the laser target via cartesian coordinates
     */
    void setPos(double x, double y, double z);

};

#include "gcode.h"

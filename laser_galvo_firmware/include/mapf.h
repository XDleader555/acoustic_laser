/**
 * mapf.h - Maps floats to a range
 *  
 * Copyright (c) 2019 Andrew Miyaguchi. All rights reserved.
 * 
 * Based on the arduino map funtion, but for floats.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#pragma once

/**
 * Maps a float to to a range
 * 
 * @param val input value
 * @param in_min lower input range
 * @param in_max upper input range
 * @param out_min lower output range
 * @param out_max upper output range
 * @return mapped float value
 */
inline float mapf(float val, float in_min, float  in_max, float  out_min, float  out_max) {
    return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

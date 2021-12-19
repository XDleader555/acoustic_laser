/**
 * Marlin 3D Printer Firmware
 * Copyright (c) 2020 MarlinFirmware [https://github.com/MarlinFirmware/Marlin]
 *
 * Based on Sprinter and grbl.
 * Copyright (c) 2011 Camiel Gubbels / Erik van der Zalm
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
 *
 */
#include "temperature.h"

/**
 * Bisect search for the range of the 'raw' value, then interpolate
 * proportionally between the under and over values.
 */
#define SCAN_THERMISTOR_TABLE(TBL,LEN) do{                            \
  uint8_t l = 0, r = LEN, m;                                          \
  for (;;) {                                                          \
    m = (l + r) >> 1;                                                 \
    if (!m) return int16_t(pgm_read_word(&TBL[0].celsius));           \
    if (m == l || m == r) return int16_t(pgm_read_word(&TBL[LEN-1].celsius)); \
    int16_t v00 = pgm_read_word(&TBL[m-1].value),                     \
          v10 = pgm_read_word(&TBL[m-0].value);                       \
         if (raw < v00) r = m;                                        \
    else if (raw > v10) l = m;                                        \
    else {                                                            \
      const int16_t v01 = int16_t(pgm_read_word(&TBL[m-1].celsius)),  \
                  v11 = int16_t(pgm_read_word(&TBL[m-0].celsius));    \
      return v01 + (raw - v00) * float(v11 - v01) / float(v10 - v00); \
    }                                                                 \
  }                                                                   \
}while(0)

float analog_to_celsius_galvo(const int raw) {
  SCAN_THERMISTOR_TABLE(temptable_1, COUNT(temptable_1));
}
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 16:04:22 2020

@author: David
"""
import datetime as d
from pysolar.solar import get_altitude, get_azimuth
from pysolar.radiation import get_radiation_direct
import numpy as np
import math


def getRadiation(day_sample, interval):
  secs = interval * 60 * sample_interval_minutes
  day = day_sample * sample_interval_days
  dt = start_date + d.timedelta(day, secs)
  alt = get_altitude(lat, lon, dt)
  azi = get_azimuth(lat, lon, dt)
  if (alt < 0):
    direct_radiation = 0
  else:
    direct_radiation = get_radiation_direct(dt, alt)
  # get_azimuth returns bearing with respect to north, positive clockwise. Rotate so x is west, y is south
  azi_rad = math.radians(270 - azi)
  alt_rad = math.radians(alt)
  sun_vec = np.array((math.cos(alt_rad) * math.cos(azi_rad), math.cos(alt_rad) * math.sin(azi_rad), math.sin(alt_rad)))
  rad = [max(0, sun_vec @ v * direct_radiation) for v in tilt_vecs]
  return rad


MT = d.timezone(d.timedelta(hours = -7))

sample_interval_minutes = 5
samples_per_day = int(60/sample_interval_minutes) * 14 + 1  # we're only sampling 5AM to 5PM

sample_interval_days = 1
samples_per_year = int(365/sample_interval_days) + 1


start_date = d.datetime(2019,12,22, 5, tzinfo = MT)

lat =  36.5
lon = -106.9
tilts_degrees = [25, 35, 45, 55, 65, 75]

tilts_rads = [math.radians(t) for t in tilts_degrees]

tilt_vecs = [np.array((0, math.cos(t), math.sin(t))) for t in tilts_rads]

panel_power = np.empty((samples_per_year, samples_per_day, len(tilt_vecs)),float)

for day in range(samples_per_year):
  for interval in range(samples_per_day):
      p = getRadiation(day, interval)
      for i in range(len(tilt_vecs)):
        panel_power[day, interval,i] = p[i]



power_day_sum = panel_power.sum(1)

np.savetxt('all_tilts_15min_daily.csv', power_day_sum, '%5.2f',',')

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


def getRadiation(day, interval):
  secs = interval * 60 * sample_interval_minutes
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
  rad = max(0, sun_vec @ tilt_vecs[tilt_idx[day]] * direct_radiation)
  return rad


MT = d.timezone(d.timedelta(hours = -7))

sample_interval_minutes = 5
samples_per_day = int(60/sample_interval_minutes) * 14 + 1  # we're only sampling 5AM to 5PM

start_date = d.datetime(2019,12,22, 5, tzinfo = MT)

lat =  36.5
lon = -106.9



tilts_degrees = [25, 45,75]

tilts_rads = [math.radians(t) for t in tilts_degrees]

tilt_vecs = [np.array((0, math.cos(t), math.sin(t))) for t in tilts_rads]

#Make a list of which tilt applies for each day of year. Entry is index in tilt arrays
#Assume change days are 2/9 (Julian 51), 3/31 (102), 9/9 (264) and 11/2 (318)

tilt_idx = [0] * 51 + [1]*(102 - 51) + [2] * (264 - 102) + [1] * (318 - 264) + [0] * (365 - 318)
panel_power = np.empty((365, samples_per_day),float)

for day in range(365):
  for interval in range(samples_per_day):
    panel_power[day, interval] = getRadiation(day, interval)



power_day_sum = panel_power.sum(1)

np.savetxt('opt_4_tilts_15min_daily.csv', power_day_sum, '%8.2f',',')

normalized_panel_power = panel_power/np.amax(panel_power)
normalized_day_sum = normalized_panel_power.sum(1)

np.savetxt('opt_4_tilts_normalized.csv', normalized_day_sum, '%8.5f', ', ')

def clipEntry(x):
  return min(x, 1.0)

def clipArray(a):
  return np.vectorize(clipEntry)(a)

def scaleClipSum(array, scale_factor):
  return clipArray(array * scale_factor).sum(1)

p125 = scaleClipSum(normalized_panel_power, 1.25)
p150 = scaleClipSum(normalized_panel_power, 1.5)
p175 = scaleClipSum(normalized_panel_power, 1.75)
p200 = scaleClipSum(normalized_panel_power, 2.0)
p250 = scaleClipSum(normalized_panel_power, 2.50)
p300 = scaleClipSum(normalized_panel_power, 3.00)
p400 = scaleClipSum(normalized_panel_power, 4.00)
p500 = scaleClipSum(normalized_panel_power, 5.00)

np.savetxt('scaled.csv', np.array([normalized_day_sum, p125, p150, p175, p200, p250, p300, p400, p500]).T, '%8.5f', ',')



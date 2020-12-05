# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 11:07:18 2020

@author: David
"""

import numpy as np
import csv
from tempfile import mkstemp
import os
import datetime as d
from pysolar.solar import get_altitude, get_azimuth
from pysolar.radiation import get_radiation_direct
from math import sin, cos, radians


def preProcess(filename):
  """
    Copies input file to a temp file, merging the date & time components into something readable by
    datetime constructor

    returns name of temp file. It is NOT open. Please delete the file to avoid clutter.

  Parameters
  ----------
  filename : string
    The file to clean

  Returns
  -------
  string
    the name of the temp file

  """

  file_desc, temp_filename = mkstemp('.csv')
  with (os.fdopen(file_desc, mode = 'w', newline = '')) as out:
    writer = csv.writer(out)
    with (open(filename)) as f:
      reader = csv.reader(f)
      # skip two header lines
      next(reader)
      next(reader)
      for row in reader:
        #  #File has the following columns
        #Year Month Day Hour Minute DHI DNI GHI Solar Zenith Angle_surface Wind_Speed Temperature
        #output combined datetime as YYYY-MM-DDTHH:MM
        row[0] = row[0] + "-" + row[1] + "-" + row[2] + "T" + row[3] + ":" + row[4]
        del row[1:5]
        del row[-1]
        writer.writerow(row)
  return temp_filename




def toStr(str_date):
  return str_date.decode('utf-8')


def readProcessedFile(filename):

  #processed file has cols
  # date_time, DHI DNI GHI Solar_zenith_Angle Surface_albedo Wind_Speed Temperature

  temp_name = preProcess(filename)
  array_types = np.dtype("U16, i4, i4, i4, f4,f4,f4, i4")

  solar_data = np.genfromtxt(temp_name, delimiter = ',', dtype = array_types, \
                             skip_header = 1,  \
                               converters={0: toStr})
  years = int(len(solar_data)/8760)
  solar_data = solar_data.reshape(years, 8760)
  os.remove(temp_name)
  return solar_data



years = 5
start_year = 2015
#MT = d.timezone(d.timedelta(hours = -7))
MT = ':-0700'
lat = 36.5
lon = -106.9

tilts_degrees = [25, 45,75]

def vecFromTilt(tilt_degrees):
  return np.array((0, cos(radians(tilt_degrees)), sin(radians(tilt_degrees))))

tilt_vecs = [vecFromTilt(t) for t in tilts_degrees]

tilt_idx = [0] * 51 + [1]*(102 - 51) + [2] * (264 - 102) + [1] * (318 - 264) + [0] * (365 - 318)

def readAllYears(filename_base):
  sd = []
  for year in range(start_year, start_year + years):
    sd = sd + [readProcessedFile(filename_base + str(year) + '.csv')]
  stack = np.stack(sd).reshape(years, 365, 24)
  return stack

def computeInsolationInternal(cos_theta, cos_beta, one_reading):

  #Insolation is computed as a combination of the direct component DNI, the diffuse sky DHI, and the
  #reflected component which uses the global horizontal irradiation GHI and the surface albedo
  #
  #       total_insolation = cos(theta) * DNI + DHI + .5 * rho * GHI * (1 - cos(beta))
  #
  # where theta is that angle between the collector normal and the sun vector, rho is surface albedo
  # and beta is the angle between the collector normal and zenith
  # ref: Resource Assessment and site selection for solar heating and cooling systems, D.S. Renné
  # in "Advances in Solar Heating and Cooling", 2016, DOI: 10.1016/B978-0-08-100301-5.00002-3

  DHI = one_reading[1]
  DNI = one_reading[2]
  GHI = one_reading[3]
  rho = one_reading[5]
  input =  cos_theta * DNI # DHI + .5 * rho * (1 - cos_beta) * GHI
  return input




def computeInsolationOneDay(day_tuples, lat, lon, timezone, collector_normal, collector_tilt):

  #if sun is below horizon return 0
  zenith = day_tuples[0][4]
  if zenith > 90:
    return 0

# get the sun location. Assume sun is in same position for same day independent of year
  date = d.datetime.strptime(day_tuples[0][0]+timezone, '%Y-%m-%dT%H:%M:%z')
  alt = 90 - zenith
  azi = get_azimuth(lat, lon, date)
  # get_azimuth returns bearing with respect to north, positive clockwise. Rotate so x is west, y is south
  azi_rad = radians(270 - azi)
  alt_rad = radians(alt)

  sun_vec = np.array((cos(alt_rad) * cos(azi_rad), cos(alt_rad) * sin(azi_rad), \

                      sin(alt_rad)))
  cos_theta = sun_vec @ collector_normal

  #cos beta is based on tilt from zenith = 90 - tilt_from_horizon
  cos_beta = cos(radians(1 - collector_tilt))
  return [computeInsolationInternal(cos_theta, cos_beta, t) for t in day_tuples]


def computeInsolationAnnualFixed(data_array, lat, lon, timezone, collector_tilt):
  insolation = np.empty(data_array.shape, np.dtype('f8'))
  collector_normal = vecFromTilt(collector_tilt)
  for day in range(365):
    for hour in range(24):
      insolation[:, day, hour] = \
        computeInsolationOneDay(data_array[:, day, hour], lat, lon, timezone, \
                                collector_normal, collector_tilt)
  ins_day = insolation.sum(2)
  max_hr = np.amax(insolation)
  max_idx = np.argmax(insolation)
  max_hr_tuple = data_array.flatten()[max_idx]
  avg = np.average(ins_day)
  print(f'{collector_tilt}, {max_hr}, {max_idx}, {max_hr_tuple}, {avg}')
  return insolation


def computeInsolationAnnualVariable(data_array, lat, lon, timezone,\
                                 collector_tilts, collector_normals, tilt_idxs):
  insolation = np.empty(data_array.shape, np.dtype('f8'))
  for day in range(365):
    for hour in range(24):
      insolation[:, day, hour] = \
        computeInsolationOneDay(data_array[:, day, hour], lat, lon, timezone, \
                                collector_normals[tilt_idxs[day]], collector_tilts[tilt_idxs[day]])
  ins_day = insolation.sum(2)
  max_hr = np.amax(insolation)
  avg = np.average(ins_day)
  print(f'{collector_tilts}, {max_hr}, {avg}')
  return insolation

def clipEntry(x):
  return min(x, 1.0)

def clipArray(a):
  return np.vectorize(clipEntry)(a)

def scaleClipSum(array, scale_factor):
  return clipArray(array * scale_factor).sum()

#%%  Execute on Ranch data

data = readAllYears('RanchNREL_data/108335_36.45_-106.94_')

insolation = computeInsolationAnnualVariable(data, lat, lon, MT, tilts_degrees, tilt_vecs, tilt_idx)

normalized_insolation = insolation / np.amax(insolation)

for s in [1.0, 1.25, 1.5, 1.75, 2.0]:
  print(s, scaleClipSum(normalized_insolation, s))





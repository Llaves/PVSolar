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




def preProcessSUNY(filename):
  """
    Copies input file to a temp file, removing all rows for 02/29, reformatting the date,
    and replacing -9900 with 0

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
      for row in reader:
        #skip rows with leap day yyyy:02-29
        if (row[0].find('02-29', 5, 10) == -1):
          row[1] = row[0] + '-' + row[1].replace(':','-')
          del row[0]
          writer.writerow(row)
  return temp_filename

def toStr(str_date):
  return str_date.decode('utf-8')

def clipPos(val):
  return max(int(val), 0)

def readSUNYFile(filename):
  temp_name = preProcessSUNY(filename)
  array_types = np.dtype("U16, i4, i4")
  solar_data = np.genfromtxt(temp_name, delimiter = ',', dtype = array_types, \
                             skip_header = 1, usecols=(0,1,2), \
                               converters={0: toStr, 1: clipPos, 2: clipPos})
  years = int(len(solar_data)/8760)
  solar_data = solar_data.reshape(years, 8760)
  os.remove(temp_name)
  return solar_data

readSUNYFile('C:/Users/David/Code/Python/PVSolar/SUNY_Ranch_Data.csv')


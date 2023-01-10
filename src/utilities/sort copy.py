import csv
import pandas as pd
import glob
import os
from csv import writer, reader

# setting the path for joining multiple files
files = "Spaghi/*.csv"

# list of merged files returned
files = glob.glob(files)


df = pd.concat(map(pd.read_csv, files), ignore_index=True)

df['time'] = pd.to_datetime(df['time'])
df = df.sort_values(by='time')

#df['time'] = str(df['time'])
#df['time'] = df['time'].apply(lambda t: t.split('       ')[1])
#df['time'] = df['time'].apply(lambda t: t.split('.')[0])

mfile = "Spaghetti.csv"
df.to_csv(mfile, index=False)

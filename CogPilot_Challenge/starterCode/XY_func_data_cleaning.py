#!/usr/bin/env python
# coding: utf-8

# In[11]:


import os
import pandas as pd
import numpy as np
import scipy as sp
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'notebook')
import seaborn as sns
sns.set_theme(style="darkgrid")

# set directories
cwd = os.getcwd()
main_dir = os.path.split(cwd)[0]
data_ils_dir = os.path.join(main_dir, 'dataPackage', 'task-ils')
data_rest_dir = os.path.join(main_dir, 'dataPackage', 'task-rest')
output_csv_dir = os.path.join(main_dir, 'dataPackage')


# In[2]:


# cap_ID format:'cp003', level format:'01B', sensor format:'lslshimmertorsoacc'
def get_dirs_to_csv(data_dir, cap_ID, level, sensor):
    # get the file direcotries for target cap_ID
    all_cap_dirs = os.listdir(data_dir)
    target_cap_dir = [d for d in all_cap_dirs if cap_ID in d]
    # get the session direcotry for target cap_ID
    target_cap_session_dir_name = [d for d in 
                                   os.listdir(os.path.join(data_dir, target_cap_dir[0])) 
                                   if os.path.isdir(os.path.join(data_dir, target_cap_dir[0],d))]
    target_cap_session_dir = os.path.join(data_dir, target_cap_dir[0], target_cap_session_dir_name[0])
    # get 3 directories of target level for target cap_ID
    target_cap_level_dir_names = [d for d in 
                                  os.listdir(target_cap_session_dir) if level in d]
    target_cap_level_dirs = [os.path.join(target_cap_session_dir, d) for d in target_cap_level_dir_names]
    # get 3 data files that contain sensor names from 3 level directories
    keywords = [sensor, 'dat']
    matched_files = []
    for d in target_cap_level_dirs:
        for f in os.listdir(d):
            if all(keyword in f for keyword in keywords) and os.path.isfile(os.path.join(d, f)):
                matched_files.append(os.path.join(d, f))
    return matched_files;


# In[3]:

def test_1():
    return (1,2)

def get_csv_freq(data_csv_dir):
    header_dir=data_csv_dir[:-7]+'hea.csv'
    df = pd.read_csv(header_dir)
    sr = df['Fs_Hz_effective'][0]
    sr = int(sr) + (sr % 1 > 0)
    return sr


# In[4]:


def get_all_data_csv_names(data_dir):
    # List of CSV file names
    csv_files = []
    # Recursively search for CSV files in the subdirectories of the current directory
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if f.endswith('.csv') and os.path.isfile(os.path.join(root, f)):
                csv_files.append(f)
    return csv_files;


# In[377]:


if __name__ == "__main__":
    all_sensor_names = find_all_sensor_names_from_files(all_csv_names)
    df = pd.DataFrame(all_sensor_names)
    df.to_csv(os.path.join(output_csv_dir, 'all_sensor_names.csv'), index=False, header=False)


# In[62]:


# produce all csv names and save to file
if __name__ == "__main__":
    all_csv_names = get_all_data_csv_names(data_ils_dir)
    df = pd.DataFrame(all_csv_names)
    df.to_csv(os.path.join(output_csv_dir, 'all_csv_names.csv'), index=False, header=False)


# In[57]:


def find_all_sensor_names_from_files(all_csv_files):
    # Keywords to search for
    keyword1 = 'stream'
    keyword2 = 'feat'
    # Find unique sensors that are found between stream_ and _feat
    unique_sensors = list(set([s[s.index(keyword1)+len(keyword1)+1:s.index(keyword2)-1] 
                               for s in all_csv_files if keyword1 in s and keyword2 in s]))
    return unique_sensors


# In[12]:

def get_head_tail_time_to_remove(csv_dir):
    folder_dir = os.path.split(csv_dir)[0]
    xp11_name = [d for d in os.listdir(folder_dir) if 'lslxp11xpcac' in d and 'dat' in d]
    xp11_dir = os.path.join(folder_dir, xp11_name[0])
    if os.path.isfile(xp11_dir):
        df = pd.read_csv(xp11_dir)
        # take only the sensor columns, drop the time column
        df1 = df.drop(df.columns[0], axis=1)
        row_sum = df1.sum(axis=1)
        # get the length of stride of 1st values and stride of last values
        occ_head = row_sum.value_counts()[row_sum[0]]
        occ_tail = row_sum.value_counts()[row_sum.tail(1).values[0]]
        # get the time points: t0 - inital time, t1 first real data, t2 last real data time, t3 last time
        if occ_head > 1: # if more stride exist
            t0 = df.iloc[0,0]
            t0_real = datetime.fromordinal(int(t0)) + timedelta(days=t0%1) - timedelta(days = 366)
            t1 = df.iloc[occ_head,0]
            t1_real = datetime.fromordinal(int(t1)) + timedelta(days=t1%1) - timedelta(days = 366)
            delta = t1_real - t0_real
            head = delta.total_seconds() 
        else: head = 0
        if occ_tail > 1: 
            t2 = df.iloc[-occ_tail,0]
            t2_real = datetime.fromordinal(int(t2)) + timedelta(days=t2%1) - timedelta(days = 366)
            t3 = df.iloc[-1,0]
            t3_real = datetime.fromordinal(int(t3)) + timedelta(days=t3%1) - timedelta(days = 366)
            delta = t3_real - t2_real
            tail = delta.total_seconds() 
        else: tail = 0
    else: 
        head, tail = (0,0) # if xp11 file do not exist, assume 0,0
    return (head, tail)
    
# plot the FFT of target 1d sensor data in df, and show lpf data using a given cut off freq
def plot_FFT(df1, sr, cut_off_freq):
    # input: cut_off_freq, sr, df1
    # Do a Fourier transform of the DataFrame
    # sampling rate
    sr = 128
    # FFT
    X = np.fft.fft(df1,axis=0)
    # number of FFT freq components
    N = len(X)
    # recover time is s for plotting 
    ts = 1./sr
    t = np.arange(0,N/sr,ts)

    # FFT bin size
    T = N/sr
    freq_bin_size = np.floor(T)
    # FFT amp
    X_amp = np.abs(X)/N

    # low pass filtered data by cut_off_freq
    X_lpf = X
    X_lpf[cut_off_freq*sr:] = 0
    Y_lpf = np.fft.ifft(X_lpf,axis=0)

    # find average amp at 1Hz bin
    # the first amp is baseline (freq=0)
    psd = X_amp[0]
    # from freq=1 to half of the specturm (f=sr/2)
    for f in range(sr//2 - 1):
        # avg amp as the root square sum of freq components in 1 Hz bin
        freq_bin = X_amp[int(1+f*freq_bin_size):int(1+(f+1)*freq_bin_size+1)]
        freq_amp_avg = np.sqrt(np.sum(freq_bin**2)/freq_bin_size)
        psd = np.append(psd, freq_amp_avg)
    #slider to plots
    
    # plot psd and lps data
    plt.figure(figsize = (12, 12))
    plt.subplot(421)
    n_psd = np.arange(sr//2-1)
    # only showing from freq=1, not showing baseline
    plt.stem(n_psd, psd[1:])
    plt.xlabel('Freq')
    plt.ylabel('Freq Amplitude')

    plt.subplot(412)
    plt.plot(t, Y_lpf, 'r')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (low pass)')


    plt.subplot(413)
    plt.plot(t[::100],Y_lpf[::100], 'r')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (downsampled)')
    
    plt.subplot(414)
    plt.plot(t, df1, 'r')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (original)')

    plt.show()


# In[24]:


if __name__ == "__main__":
    test_csv = get_dirs_to_csv(data_ils_dir, 'cp030', '04B', 'lslrespitrace')[0]


# In[25]:


if __name__ == "__main__":
    df = pd.read_csv(test_csv)
    df1 = df.iloc[:,1]
    sr = get_csv_freq(test_csv)
    plot_FFT(df1, sr, 20)


# In[26]:



# In[ ]:





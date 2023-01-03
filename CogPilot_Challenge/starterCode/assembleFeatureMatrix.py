import sys
import numpy as np
import pandas as pd
from optparse import OptionParser
import os
from scipy.stats import entropy
from scipy import signal
import scipy.stats as spstats
import fnmatch
from datetime import datetime
from scipy.stats import skew
from scipy.stats import kurtosis
from scipy.stats import t
from scipy.optimize import fsolve
import scipy.special as sc

#Extracts aggregate features per run from raw eye tracking and oculomotor event data, and builds a single feature matrix for use as input to train and validate a predictive model. If the feature matrix file already exists from a prior run of getFeatureMatrix(), you can save time by specifying useExisting=True to load it directly from the file rather than recomputing it from scratch. 

# Research was sponsored by the United States Air Force Research Laboratory and the
# United States Air Force Artificial Intelligence Accelerator and was accomplished
# under Cooperative Agreement Number FA8750-19-2-1000. The views and conclusions
# contained in this document are those of the authors and should not be interpreted
# as representing the official policies, either expressed or implied, of the United
# States Air Force or the U.S. Government. The U.S. Government is authorized to
# reproduce and distribute reprints for Government purposes notwithstanding any
# copyright notation herein.

def getFeatureMatrix(dataDir, filePath, useExisting):
    if (useExisting): 
        if (os.path.exists(filePath)):
            print("Found precomputed feature matrix.");
            featMatDF = pd.read_csv(filePath);
            print("Loaded into a dataFrame.");
            return featMatDF;
        else:
            print("Cannot use existing feature matrix because specified file was not found. Recomputing it from scratch.");
    
    subjDirs = [f.path for f in os.scandir(dataDir) if f.is_dir()];
    
    dfHeader = ['Subject', 'Session', 'Run',
                'overall_gaze_entropy_LX', 'psd_max_LX', 'psd_freq_of_max_LX',
                'overall_gaze_entropy_LY', 'psd_max_LY', 'psd_freq_of_max_LY',
                'overall_gaze_entropy_LZ', 'psd_max_LZ', 'psd_freq_of_max_LZ',
                'overall_gaze_entropy_RX', 'psd_max_RX', 'psd_freq_of_max_RX',
                'overall_gaze_entropy_RY', 'psd_max_RY', 'psd_freq_of_max_RY',
                'overall_gaze_entropy_RZ', 'psd_max_RZ', 'psd_freq_of_max_RZ',
                'eyes_closed_fraction_L', 'eyes_closed_fraction_R',
                'pupil_diam_mean_L', 'pupil_diam_stdev_L', 'pupil_diam_skew_L', 'pupil_diam_kurt_L',
                'pupil_diam_mean_R', 'pupil_diam_stdev_R', 'pupil_diam_skew_R', 'pupil_diam_kurt_R',
                'fix_dur_mean', 'fix_dur_stdev', 'fix_dur_skew', 'fix_dur_kurt',
                'fix_density_mean', 'fix_density_stdev', 'fix_density_skew', 'fix_density_kurt',
                'sac_main_seq_mean', 'sac_main_seq_stdev',
                'sac_peak_vel_mean', 'sac_peak_vel_stdev'];
    
    #walks through the directory structure of the raw data
    featMat = [];
    ctr = 1;
    for subjd in subjDirs:

        sessDirs = [f.path for f in os.scandir(subjd) if f.is_dir()];
        print('Processing subject '+str(ctr)+" of "+str(len(subjDirs))+": "+os.path.basename(subjd));
        ctr = ctr + 1;
        for sessd in sessDirs:
            runDirs = [f.path for f in os.scandir(sessd) if f.is_dir()];
            for rund in runDirs:
                dataFiles = [f.path for f in os.scandir(rund) if (f.is_file() and not f.name.startswith('.'))];
                toks = rund.split(os.path.sep);
                subj = toks[-3];
                sess = toks[-2];
                run = toks[-1];
                
                rawEyeFile = fnmatch.filter(dataFiles, '*lslhtcviveeye*.csv');
                dfraw = pd.read_csv(rawEyeFile[0]);
                
                if (len(dfraw) == 0):
                    continue;
                
                timeStr = dfraw['time_dn'];
                
                datalen = len(timeStr);
                if (datalen < 10):
                    continue;

                #if there is even one corrupted date-time string, skip this whole run.
                try:
                    timesMillis = [convertTimeStrToMillis(f) for f in timeStr];
                except ValueError:
                    print("corrupted timestamp string, skipping run = "+run+", subj = "+subj+", sess = "+sess);
                    continue;

                ocuEvtsFile = fnmatch.filter(dataFiles, '*_ocuevts_*.csv');
                if (len(ocuEvtsFile) < 1):
                    print("No oculomotor events file found for run "+run+", subj = "+subj+", sess = "+sess);
                    continue;
                try:
                    dfocu = pd.read_csv(ocuEvtsFile[0]);
                except pd.errors.EmptyDataError:
                    print("Empty oculomotor events file. Skipping.");
                    continue;
                
                if (dfocu.shape[0] < 10):
                    continue;

                gazeFeats = extractRawEyeFeats(dfraw, timesMillis);
                
                ocuEvtFeats = extractOcuEvtFeats(dfraw, dfocu);
                dfrow = [subj, sess, run]
                dfrow = dfrow + gazeFeats + ocuEvtFeats;
                featMat.append(dfrow)

    featMatDF = pd.DataFrame(featMat, columns = dfHeader);
    if (filePath != None):
        print("Saving feature matrix to file.");
        featMatDF.to_csv(filePath);

    print("Processing complete. Returning feature matrix data frame.");
    return featMatDF;

def convertTimeStrToMillis(timeStr):
    
    millisec = float(timeStr) * 1000;
    return millisec;

def extractRawEyeFeats(df, timesMillis):
    
    diffTimes = np.diff(timesMillis);
    fs = np.mean(1./diffTimes);
    gazeFeatsLX = getSpectralFeatures(df['gaze_direction_l_x'].values, fs);
    gazeFeatsLY = getSpectralFeatures(df['gaze_direction_l_y'].values, fs);
    gazeFeatsLZ = getSpectralFeatures(df['gaze_direction_l_z'].values, fs);

    gazeFeatsRX = getSpectralFeatures(df['gaze_direction_r_x'].values, fs);
    gazeFeatsRY = getSpectralFeatures(df['gaze_direction_r_y'].values, fs);
    gazeFeatsRZ = getSpectralFeatures(df['gaze_direction_r_z'].values, fs);

    eyeClosedFracL = getFracTimeEyeClosed(df['eye_openness_l'].values, 0.5);
    eyeClosedFracR = getFracTimeEyeClosed(df['eye_openness_r'].values, 0.5);

    pupilFeatsL = getPupilFeatures(df['pupil_diameter_l_mm'].values);
    pupilFeatsR = getPupilFeatures(df['pupil_diameter_r_mm'].values);
    
    eyeFeatsAll = gazeFeatsLX + gazeFeatsLY + gazeFeatsLZ + gazeFeatsRX + gazeFeatsRY + gazeFeatsRZ + [eyeClosedFracL, eyeClosedFracR] + pupilFeatsL + pupilFeatsR;
    
    return eyeFeatsAll;

def getFracTimeEyeClosed(eoSignal, thresh):
    closedSamples = np.where(eoSignal <= thresh);
    timeEyeClosed = np.max(closedSamples[0].shape);
    fracTimeEyeClosed = timeEyeClosed/np.max(eoSignal.shape);

    return fracTimeEyeClosed;
    
def getPupilFeatures(pdSignal):

     meanPD = np.mean(pdSignal);
     stdevPD = np.std(pdSignal);
     skewPD = skew(pdSignal);
     kurtPD = kurtosis(pdSignal);

     return [meanPD, stdevPD, skewPD, kurtPD];
     
#compute the overall spectral entropy of a continuous-valued signal, as well as the peak of the power spectral density.
def getSpectralFeatures(rawSignal, fs):
     f, psd = signal.welch(rawSignal, fs); #defaults to: hanning window, 256 samples per segment. Returns mean across segments.
     psdMaxPower = max(psd);
     psdMaxPowerIdx = np.argmax(psd)
     psdFreqOfMax = f[psdMaxPowerIdx];

     #Spectral Entropy is defined to be the Shannon Entropy of the power spectral density of the data.
     #Step 1: Normalize the PSD by dividing it by the total PSD sum
     normPSD = psd/sum(psd);
     
     #Step 2: Calculate power spectral entropy
     overallEntropy = -np.sum(normPSD*np.log2(psd));

     return [overallEntropy, psdMaxPower, psdFreqOfMax];

#Extract features pertaining to oculomotor events: fixations and saccades.
def extractOcuEvtFeats(dfRawEye, dfOcuEvt):
    
    eoSignal = dfRawEye['eye_openness_l'].values;
    eyeOpenIdxs = np.where(eoSignal > 0.5);
    eoIdxs = eyeOpenIdxs[0]

    fixFeats = getFixationFeats(dfOcuEvt, dfRawEye, eoIdxs[:-2]);
    sacFeats = getSaccadeFeats(dfOcuEvt, dfRawEye, eoIdxs[:-2]);
    
    return fixFeats + sacFeats;

#Computes aggregate statistics of fixation durations and densities across each run.
def getFixationFeats(dfOcuEvt, dfRawEye, eoIdxs):

    fixSeq = dfOcuEvt['FixationSeq'].values;
    timeCol = dfOcuEvt['Timestamp'].values;
    gazeX = dfRawEye['gaze_direction_l_x'].values;
    gazeY = dfRawEye['gaze_direction_l_y'].values;
    gazeZ = dfRawEye['gaze_direction_l_z'].values;

    fixEO = fixSeq[eoIdxs];
    timeEO = timeCol[eoIdxs];
      
    fixDurs = getFixDurations(fixEO, timeEO);
    fixDens = getFixDensities(fixEO, timeEO, gazeX[eoIdxs], gazeY[eoIdxs], gazeZ[eoIdxs]);

    meanFixDur = np.mean(fixDurs);
    stdevFixDur = np.std(fixDurs);
    skewFixDur = skew(fixDurs);
    kurtFixDur = kurtosis(fixDurs);
    
    meanFixDen = np.mean(fixDens);
    stdevFixDen = np.std(fixDens);
    skewFixDen = skew(fixDens);
    kurtFixDen = kurtosis(fixDens);
    
    return [meanFixDur, stdevFixDur, skewFixDur, kurtFixDur,
            meanFixDen, stdevFixDen, skewFixDen, kurtFixDen];

def getFixDurations(fixEO, timeEO):
    fixDurs = [];
    uniqueFixNums = set(fixEO);
    for fn in uniqueFixNums:
        if (fn < 0):
            continue;

        curFixIdxsArr = np.where(fixEO == fn);
        curFixIdxs = curFixIdxsArr[0];
        curFixTimes = timeEO[curFixIdxs];

        startTime = curFixTimes[0];
        endTime = curFixTimes[-1];

        curFixDur = endTime-startTime;
        fixDurs.append(curFixDur);

    return fixDurs;

def getFixDensities(fixEO, timeEO, gazeEOx, gazeEOy, gazeEOz):
    fixDens = [];
    uniqueFixNums = set(fixEO);
    for fn in uniqueFixNums:

        if (fn < 0):
            continue;

        curFixIdxsArr = np.where(fixEO == fn);
        curFixIdxs = curFixIdxsArr[0];
        curFixTimes = timeEO[curFixIdxs];

        startTime = curFixTimes[0];
        endTime = curFixTimes[-1];

        curFixDen = computeDispersion(gazeEOx[curFixIdxs], gazeEOy[curFixIdxs], gazeEOz[curFixIdxs]);
        fixDens.append(curFixDen);

    return fixDens;

def computeDispersion(gazeX, gazeY, gazeZ):

    centroidX = np.mean(gazeX);
    centroidY = np.mean(gazeY);
    centroidZ = np.mean(gazeZ);
    
    offsetsXsq = np.square(gazeX - centroidX);
    offsetsYsq = np.square(gazeY - centroidY);
    offsetsZsq = np.square(gazeZ - centroidZ);

    dispersion = np.sqrt(np.mean(offsetsXsq) + np.mean(offsetsYsq) + np.mean(offsetsZsq));

    return dispersion;

def getSaccadeFeats(dfOcuEvt, dfRawEye, eoIdxs):

    sacSeq = dfOcuEvt['SaccadeSeq'].values;
    timeCol = dfOcuEvt['Timestamp'].values;
    gazeX = dfRawEye['gaze_direction_l_x'].values;
    gazeY = dfRawEye['gaze_direction_l_y'].values;
    gazeZ = dfRawEye['gaze_direction_l_z'].values;

    sacEO = sacSeq[eoIdxs];
    timeEO = timeCol[eoIdxs];

    sacFeats = computeSacMetrics(sacEO,
                                 timeEO,
                                 gazeX[eoIdxs],
                                 gazeY[eoIdxs],
                                 gazeZ[eoIdxs]);

    return sacFeats;

#Computes aggregate statistics of saccade main sequence and peak velocity across each run.
def computeSacMetrics(sacEO, timeEO, gazeEOx, gazeEOy, gazeEOz):

    sacAmpls = [];
    sacPkVels = [];
    sacDurs = [];
    
    uniqueSacNums = set(sacEO);
    for sn in uniqueSacNums:

        if (sn < 0):
            continue;

        curSacIdxsArr = np.where(sacEO == sn);
        curSacIdxs = curSacIdxsArr[0];
        if (len(curSacIdxs) < 2):
            continue;
        
        curSacTimes = timeEO[curSacIdxs];
        startTime = curSacTimes[0];
        endTime = curSacTimes[-1];

        curSacDur = endTime-startTime;

        curSacGazeX = gazeEOx[curSacIdxs];
        curSacGazeY = gazeEOy[curSacIdxs];
        curSacGazeZ = gazeEOz[curSacIdxs];
        
        xvel = np.diff(curSacGazeX);
        yvel = np.diff(curSacGazeY);
        zvel = np.diff(curSacGazeZ);

        curSacAmpl = np.sqrt(np.square(curSacGazeX[-1] - curSacGazeX[0]) +
                             np.square(curSacGazeY[-1] - curSacGazeY[0]) +
                             np.square(curSacGazeZ[-1] - curSacGazeZ[0]));
        
        curSacVels = np.sqrt(np.square(xvel) +
                             np.square(yvel) +
                             np.square(zvel));

        curSacPkVel = np.percentile(curSacVels, 99);

        sacPkVels.append(curSacPkVel);
        sacDurs.append(curSacDur);
        sacAmpls.append(curSacAmpl);
        
    X = np.array(sacAmpls);
    y = np.array(sacPkVels)*np.array(sacDurs);

    [p, V] = np.polyfit(X, y, 1, full=False, cov=True);
    stdErr = np.sqrt(np.diag(V));
    df = y.shape[0]-2; #dof = N - k - 1, where N = # input data points and k = # variables = 1.

    ## The following section is translated from polyparci matlab plugin code.
    
    alpha = 0.95;   
    def tstat(tvals):
        #Function to calculate t-statistic for p = alpha and v = degrees of freedom
        cdfvals = t_cdf(tvals, df);
        return alpha - cdfvals;
    
    T = fsolve(tstat, 1); #Calculate t-statistic for p = alpha and v = degrees of freedom   
    T = abs(T); #Critical +ve value from t-distribution   
    tsA = T * -1
    tsB = T; #Create vector of t-statistic values
    
    ciStep1A = stdErr * tsA;
    ciStep1B = stdErr * tsB;
    ciA = ciStep1A + p;
    ciB = ciStep1B + p;

    ## End translation from polyparci
    
    sacMainSeqMean = p[0];
    sacMainSeqStdev = ciB[0] - ciA[0];

    sacPeakVelMean = np.mean(sacPkVels);
    sacPeakVelStdev = np.std(sacPkVels);
    
    return [sacMainSeqMean, sacMainSeqStdev, sacPeakVelMean, sacPeakVelStdev];
    

#Translated from polyparci matlab plugin code.
def t_cdf(t,v):
    # Translated from Matlab plugin code:
    # t_cdf(t,v) calculates the cumulative t-distribution probability
    #   given the t-statistic t and degrees-of-freedom v.  The
    #   routine to calculate the inverse t-distribution uses this,
    #   tstat, and the fzero call.  Compared to the Statistics
    #   Toolbox function tcdf and tinv, t_cdf and T have
    #   relative errors of about 1E-12.

    IBx = v/(np.square(t) + v);               # x for IxZW NOTE: function of t-statistic
    IBZ = v/2;                                # Z for IxZW
    IBW = 0.5;                                # W for IxZW
    Ixzw = sc.betainc(IBx, IBZ, IBW);         # Incomplete beta function
    PT = 1-0.5*Ixzw;                          # Cumulative t-distribution
    return PT;
        
    
if __name__ == '__main__':
    sys.exit(main())

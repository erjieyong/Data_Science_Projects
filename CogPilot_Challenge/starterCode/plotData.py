import sys
import numpy as np
import pandas as pd
from optparse import OptionParser
import os
import matplotlib.pyplot as plt
import scipy.stats as scistats

# Helper functions for data loading and visualization.

# Research was sponsored by the United States Air Force Research Laboratory and the
# United States Air Force Artificial Intelligence Accelerator and was accomplished
# under Cooperative Agreement Number FA8750-19-2-1000. The views and conclusions
# contained in this document are those of the authors and should not be interpreted
# as representing the official policies, either expressed or implied, of the United
# States Air Force or the U.S. Government. The U.S. Government is authorized to
# reproduce and distribute reprints for Government purposes notwithstanding any
# copyright notation herein.

def loadTimeSeries(dataRoot, subject, sessLabel, expType, modality, runLabel):
    
    subjRunDataDir = dataRoot + os.path.sep + expType + os.path.sep + subject + os.path.sep + sessLabel + os.path.sep + runLabel;
    modalityDataFile = "";
    
    if (modality.find("feat-perfmetric") != -1):
        modalityDataFile = subject+"_"+sessLabel+"_"+expType+"_stream-"+modality+"_"+runLabel+".csv";
    else:
        modalityDataFile = subject+"_"+sessLabel+"_"+expType+"_stream-"+modality+"_feat-chunk_"+runLabel+"_dat.csv";
    
    fullDataFile = subjRunDataDir + os.path.sep + modalityDataFile;
    dfEDA = pd.read_csv(fullDataFile);
    
    return dfEDA;

def plotTimeSeries(df, subject, sess, run, dataColumn, startIdx, endIdx):

    if (not isinstance(dataColumn, list)):
        dataColumn = [dataColumn];

    for c in dataColumn:
        plt.plot(df['time_dn'][startIdx:endIdx], df[c][startIdx:endIdx], label = c);
    plt.xlabel('Time');
    plt.title('Data excerpt for \nSubject: '+subject+', Session: '+sess+', Run: '+run);
    if (len(dataColumn) > 1):
        #plt.legend();
        plt.legend(bbox_to_anchor=(1.04,0.5), loc="center left", borderaxespad=0)
    else:
        plt.ylabel(dataColumn[0]);
        
    plt.show();
        
    

def plotAggFeat(df, dataColumn):

    plt.plot(df[dataColumn]);
    plt.xlabel('Runs');
    plt.ylabel(dataColumn);


def getTargetRows(featDF, perfDF, diffLevel):

    perfMetricsForDL = perfDF[perfDF['difficulty'] == diffLevel];
    perfSubj = perfMetricsForDL['subject'];
    featSubj = ['sub-cp'+str(item).zfill(3) for item in perfSubj];

    perfSes = perfMetricsForDL['date'];
    featSes = ['ses-'+str(item) for item in perfSes];

    perfRun = perfMetricsForDL['run'];
    featRun = ['level-'+str(diffLevel).zfill(2)+'B_run-'+str(item).zfill(3) for item in perfRun];

    subjRowsDF = featDF[featDF['Subject'].isin(featSubj)];
    sesRowsDF = subjRowsDF[subjRowsDF['Session'].isin(featSes)];
    runRowsDF = sesRowsDF[sesRowsDF['Run'].isin(featRun)];

    return runRowsDF;

def alignFeatPerfRows(featDF, perfDF):

    newFeatDF = featDF.copy(deep=True);
    newPerfDF = perfDF.copy(deep=True);

    featKeyCol = newFeatDF['Subject']+"-"+newFeatDF['Session']+"-"+newFeatDF['Run'];
    
    perfSubj = perfDF['subject'];
    newPerfDF['Subject'] = ['sub-cp'+str(item).zfill(3) for item in perfDF['subject']];
    newPerfDF['Session'] = ['ses-'+str(item) for item in perfDF['date']];

    diffArr = ['level-'+str(item).zfill(2)+'B_' for item in perfDF['difficulty']];
    runArr = ['run-'+str(item).zfill(3) for item in perfDF['run']];
    newPerfDF['Run'] = np.char.add(diffArr, runArr);

    perfKeyCol = newPerfDF['Subject']+"-"+newPerfDF['Session']+"-"+newPerfDF['Run'];

    newFeatDF['featKey'] = featKeyCol;
    newPerfDF['perfKey'] = perfKeyCol;
    
    joinDF = newFeatDF.merge(newPerfDF, left_on='featKey', right_on='perfKey');

    return joinDF;

def vizAggFeat_bySubj(featDF, perfDF, diffLevel, aggFeatColumn):

    meanAggFeat_bySubj = [];
    stdevAggFeat_bySubj = [];
    
    featMatDL = getTargetRows(featDF, perfDF, diffLevel);

    subjCol = featDF['Subject'];
    usubj = set(subjCol);
    for s in usubj:
        subjRowsDL = featMatDL[featMatDL['Subject'] == s];
        allAggFeat_DL = subjRowsDL[aggFeatColumn]
        meanAggFeat_bySubj.append(np.mean(allAggFeat_DL));
        stdevAggFeat_bySubj.append(np.std(allAggFeat_DL));

    x_pos = np.arange(len(usubj));
    plt.bar(x_pos, meanAggFeat_bySubj, yerr=stdevAggFeat_bySubj, alpha=0.5, ecolor='black', capsize=10);
    plt.xlabel('Subject');
    plt.xticks(x_pos, labels=usubj, rotation=90);
    plt.ylabel(aggFeatColumn)
    plt.title('Mean Values by Subject across Runs for '+aggFeatColumn+"\nDifficulty Level = "+str(diffLevel));
    plt.show();
    

def vizAggFeat_perfErr(featDF, perfDF, aggFeatColumn):

    joinDF = alignFeatPerfRows(featDF, perfDF);
    
    x = joinDF[aggFeatColumn];

    cumErr = joinDF['cumulative_glideslope_error_deg'] + joinDF['cumulative_localizer_error_deg'] + joinDF['cumulative_airspeed_error_kts'];
    
    y = cumErr;

    pearsonCorr = scistats.pearsonr(x, y);

    plt.scatter(x, y);
    plt.xlabel(aggFeatColumn);
    plt.ylabel('Cumulative Performance Error');
    plt.title('Performance Error as a Function of '+aggFeatColumn+"\nOver All Subjects and Runs\n Pearson Correlation = "+str(pearsonCorr));
    plt.show();

if __name__ == '__main__':
    sys.exit(main())          

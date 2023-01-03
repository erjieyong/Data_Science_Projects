import sys
import numpy as np
import pandas as pd
from optparse import OptionParser
import os
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn import svm
from sklearn.preprocessing import label_binarize
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from scipy.stats import zscore
import scipy.stats as scistats
from sklearn import decomposition

#run this as:
#  python trainModel.py -i <feature matrix obtained via assembleFeatureMatrix.py> -r <path to training set outcomes file>  -v <path to validation set outcomes file> -o <directory for saving validation and testing outputs> -t <output file to save test set predictions (optional)> -m <task to execute: either "PerfErr" or "DifficultyLevel">

#Pipeline for model training, validation, and obtaining predictions for the test set using the model. The user can specify whether to execute the pipeline for the DifficultyLevel or the PerfErr task.

# Research was sponsored by the United States Air Force Research Laboratory and the
# United States Air Force Artificial Intelligence Accelerator and was accomplished
# under Cooperative Agreement Number FA8750-19-2-1000. The views and conclusions
# contained in this document are those of the authors and should not be interpreted
# as representing the official policies, either expressed or implied, of the United
# States Air Force or the U.S. Government. The U.S. Government is authorized to
# reproduce and distribute reprints for Government purposes notwithstanding any
# copyright notation herein.

def main():
    parser = OptionParser()
    parser.add_option('-i', '--inFeatMatFile', action="store", dest="inFeatMatFile", default=None, help="The input file containing the feature matrix.")
    parser.add_option('-m', '--modelType', action="store", dest="modelType", default=None, help="Keyword specifying the task being solved by this model:either \"DifficultyLevel\" or \"PerfErr\".")
    parser.add_option('-r', '--trainOutcomesFile', action="store", dest="trainOutcomesFile", default=None, help="Input file of training set outcomes.");
    parser.add_option('-v', '--valOutcomesFile', action="store", dest="valOutcomesFile", default=None, help="Input file of validation set outcomes.");
    parser.add_option('-t', '--testPredOutputFile', action="store", dest="testPredOutputFile", default=None, help="If specified, will run trained model on test subjects and save the predictions to this file path.")
    parser.add_option('-o', '--outDir', action="store", dest="outDir", default=None, help="Directory to save output validation ROC curves and other results.");
    
    (options, args) = parser.parse_args()

    featMatDF = pd.read_csv(options.inFeatMatFile);
    trainOutcomesDF = pd.read_csv(options.trainOutcomesFile);
    valOutcomesDF = pd.read_csv(options.valOutcomesFile);

    #Extract train, validation, and test subsets from the feature matrix.
    trainMatDF = featMatDF.merge(trainOutcomesDF, how='inner', on=['Subject', 'Session', 'Run']);
    valMatDF = featMatDF.merge(valOutcomesDF, how='inner', on=['Subject', 'Session', 'Run']);
    testMatDF = formTestMat(featMatDF, trainOutcomesDF, valOutcomesDF);

    featCols = ['OverallGazeEntropyLX', 'psdMaxLX', 'psdFreqOfMaxLX',
                'OverallGazeEntropyLY', 'psdMaxLY', 'psdFreqOfMaxLY',
                'OverallGazeEntropyLZ', 'psdMaxLZ', 'psdFreqOfMaxLZ',
                'OverallGazeEntropyRX', 'psdMaxRX', 'psdFreqOfMaxRX',
                'OverallGazeEntropyRY', 'psdMaxRY', 'psdFreqOfMaxRY',
                'OverallGazeEntropyRZ', 'psdMaxRZ', 'psdFreqOfMaxRZ',
                'EyesClosedFractionL', 'EyesClosedFractionR',
                'PupilDiamMeanL', 'PupilDiamStdevL', 'PupilDiamSkewL', 'PupilDiamKurtL',
                'PupilDiamMeanR', 'PupilDiamStdevR', 'PupilDiamSkewR', 'PupilDiamKurtR',
                'FixDurMean', 'FixDurStdev', 'FixDurSkew', 'FixDurKurt',
                'FixDensityMean', 'FixDensityStdev', 'FixDensitySkew', 'FixDensityKurt',
                'SacMainSeqMean', 'SacMainSeqStdev',
                'SacPeakVelMean', 'SacPeakVelStdev'];
    
    if (options.modelType == "DifficultyLevel"):

        inclDiffLevels = [1, 4]; #The task is only to distinguish between difficulty levels 1 and 4.
        numPCs = 0;
        [clf, pcaSetup_diffLevels] = trainDiffPredictionModel(trainMatDF, inclDiffLevels, featCols, numPCs); 
        validateDiffPredictionModel(valMatDF, pcaSetup_diffLevels, inclDiffLevels, featCols, clf, options.outDir);
            
    elif (options.modelType == "PerfErr"):
        numPCs = 2;
        [reg, pcaSetup_perfErr] = trainPerfErrPredictionModel(trainMatDF, featCols, numPCs);
        validatePerfErrPredictionModel(valMatDF, pcaSetup_perfErr, featCols, reg, options.outDir);
        
            

#Extracts test subset of the feature matrix by excluding runs from training and validation subjects.
def formTestMat(featMatDF, trainOutcomesDF, valOutcomesDF):
    allSubjs = featMatDF['Subject'];
    trainSubjs = trainOutcomesDF['Subject'];
    valSubjs = valOutcomesDF['Subject'];

    utrainSubjs = list(set(trainSubjs));
    uvalSubjs = list(set(valSubjs));
    
    testFeatMatDF1 = featMatDF[~featMatDF.Subject.str.contains('|'.join(utrainSubjs))];    
    testFeatMatDF = testFeatMatDF1[~testFeatMatDF1.Subject.str.contains('|'.join(uvalSubjs))];
    
    utestSubjs = list(set(testFeatMatDF['Subject']));

    return testFeatMatDF;

#Trains a simple linear regression model for predicting TotalFlightError by fitting to the input features of the training dataset.
def trainPerfErrPredictionModel(trainMatDF, featCols, numPCs):

    subTrainMatDF = trainMatDF;
    
    X = subTrainMatDF[featCols];
    y = subTrainMatDF["Cumulative_Error"];

    Xz = zscore(X);
    
    #If desired, reduce dimensionality using Principal Components Analysis (PCA)
    pcaSetup = None;
    if (numPCs > 0):
        pcaSetup = decomposition.PCA(n_components=numPCs);
        pcaSetup.fit(Xz);
        Xz = pcaSetup.transform(Xz)
        
    mdl = LinearRegression().fit(Xz, y);

    return [mdl, pcaSetup];

#Performs validation of the trained performance error prediction model by computing mean squared error of predicted vs. actual Flight Performance Error values.
def validatePerfErrPredictionModel(valMatDF, pcaSetup, featCols, mdl, outDir):
    subValMatDF = valMatDF;
    
    X = subValMatDF[featCols];
    Xz = zscore(X);   
    if (pcaSetup is not None):
        Xz = pcaSetup.transform(Xz);
        
    y = subValMatDF['Cumulative_Error'];

    y_pred = mdl.predict(Xz);

    mse = mean_squared_error(y, y_pred);
    pearsonCorr = scistats.pearsonr(y, y_pred);
    [spCorr, spPval] = scistats.spearmanr(y, y_pred);
    
    plt.scatter(y, y_pred);
    lims = [min(min(y), min(y_pred)), max(max(y), max(y_pred))];
    plt.xlim(lims);
    plt.ylim(lims);
    plt.xlabel('Actual');
    plt.ylabel('Predicted');
    plt.title('Total Flight Error: Predicted vs. Actual\n MSE = '+
              str(mse)+"\nPearson Correlation: "+str(pearsonCorr)+
              "\nSpearman Correlation: ("+str(spCorr)+", "+str(spPval)+")");
    plt.savefig(outDir+os.path.sep+'valPerfErr_pred2actual.png', format='png');
    
#Trains a classifier for identifying difficulty level based on hte input features from the training dataset. The difficulty levels to be distinguished by the classifier are specified as parameters. Only the runs corresponding to these difficulty levels are included in training, validation, and testing of this classifier.
def trainDiffPredictionModel(trainMatDF, inclDiffLevels, featCols, numPCs):

    subTrainMatDF = trainMatDF.loc[trainMatDF['Difficulty'].isin(inclDiffLevels)];
    
    X = subTrainMatDF[featCols];
    y = subTrainMatDF['Difficulty'];
    
    #normalize the feature matrix
    Xz = zscore(X);
    
    #If desired, reduce dimensionality using Principal Components Analysis (PCA)
    pcaSetup = None;
    if (numPCs > 0):
        pcaSetup = decomposition.PCA(n_components=numPCs);
        pcaSetup.fit(Xz);
        Xz = pcaSetup.transform(Xz)
        
    clf = svm.SVC(probability=True);
    clf.fit(Xz, y);
    
    return [clf, pcaSetup];

#Validation of the difficulty level classifier model. Constructs an ROC Curve and computes area under the curve to quantify how well the model performs.
def validateDiffPredictionModel(valMatDF, pcaSetup, inclDiffLevels, featCols, clf, outDir):

    subValMatDF = valMatDF.loc[valMatDF['Difficulty'].isin(inclDiffLevels)];

    n_classes = len(inclDiffLevels);
    
    X = subValMatDF[featCols];
    Xz = zscore(X);
    if (pcaSetup is not None):
        Xz = pcaSetup.transform(Xz);
    y_actual = subValMatDF['Difficulty'].values;
    y_pred = clf.predict(Xz);
    
    probas = clf.predict_proba(Xz);
    
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    print("Actual = "+str(y_actual));
    print("Predicted = "+str(y_pred));
    print("Model's Confidence Probabilities = "+str(probas));
    fpr, tpr, _ = roc_curve(y_actual, probas[:,0], pos_label=inclDiffLevels[0]);
    roc_auc = auc(fpr, tpr);
    plt.figure(figsize=(5,5));
    
    plt.plot(fpr, tpr, lw=2);
    
    plt.xlim([-0.05, 1.05]);
    plt.ylim([-0.05, 1.05]);
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve for Validation Set. AUC = '+str(roc_auc));
    plt.savefig(outDir+os.path.sep+'valDiffLevelROC.png', format='png');
    

if __name__ == '__main__':
    sys.exit(main())

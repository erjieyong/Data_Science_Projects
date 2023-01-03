#Tobii format:
# Recording timestamp	Eyetracker timestamp	Eyepos3d_Left.x	Eyepos3d_Left.y	Eyepos3d_Left.z	Eyepos3dRel_Left.x	Eyepos3dRel_Left.y	Eyepos3dRel_Left.z	Gaze2d_Left.x	Gaze2d_Left.y	Gaze3d_Left.x	Gaze3d_Left.y	Gaze3d_Left.z	PupilDiam_Left	Validity_Left	Eyepos3d_Right.x	Eyepos3d_Right.y	Eyepos3d_Right.z	Eyepos3dRel_Right.x	Eyepos3dRel_Right.y	Eyepos3dRel_Right.z	Gaze2d_Right.x	Gaze2d_Right.y	Gaze3d_Right.x	Gaze3d_Right.y	Gaze3d_Right.z	PupilDiam_Right	Validity_Right	Event value	Event message

#We use the PyTrack-NTU library to extract saccade and fixation events from the tobii-format eye tracking data provided by the HTC Vive Eye headset. Install as follows:
#python3 -m pip install PyTrack-NTU
#https://readthedocs.org/projects/pytrack-ntu/downloads/pdf/latest/
#https://pypi.org/project/PyTrack-NTU/

#pip install pyxdf
#https://github.com/sccn/xdf
#https://pypi.org/project/pyxdf/

import sys
from PyTrack.formatBridge import toBase
from PyTrack.Experiment import Experiment
from PyTrack.Stimulus import Stimulus
from pandas import DataFrame
import pandas as pd
import pyxdf
import numpy as np
import pprint
import os

import scipy.io as sio
import h5py
import PyTrack

import csv

def extractSaccFixDataStream(dataFilePath, outFilePathRoot):
    splitInPath = dataFilePath.split( os.sep );

    skipsubjs = []; 
    for dirpath, dirnames, filenames in os.walk(dataFilePath):
        
        splitdir = dirpath.split( os.sep );
        
        structure = os.path.join(outFilePathRoot, os.sep.join(splitdir[len(splitInPath):]));
        if not os.path.isdir(structure):
            os.mkdir(structure)
        #else:
            #print("Folder already exists!")

        gotFile = False;
        for fname in filenames:
            if (fname.startswith(tuple(skipsubjs))):
                continue;
            
            if "lslhtcviveeye" not in fname:
                continue

            if (fname.endswith(".mat")):
                continue;

            if (fname.startswith(".")):
                continue;

            print("Processing: "+str(fname));
            full_fname = os.path.join(dirpath, fname);
            data = None;
            header = None;
            with open(full_fname, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                header = next(reader)
                data = np.array(list(reader)).astype(float)

            a = data;
            if (np.size(a,0) < 50):
                continue;
            
            data = a[~np.isnan(a).any(axis=1)];

            fandext = os.path.splitext(fname)
            
            exportToTobiiTXT_base(data, header, fandext[0], structure);
                
            tobiiBase = getOutFileName(fandext[0], 'tobii');
            tobiifn = os.path.join(structure, tobiiBase);
            
            pytrkfn = getOutFileName(fandext[0], 'pytrk');
            fullPytrkfn = os.path.join(structure, pytrkfn);
        
            df = toBase(filename=tobiifn, et_type="tobii", start='1', stop='2');
            
            newTimeCol = convertTimeMillis2Days(df['Timestamp']);
            df['Timestamp'] = newTimeCol;
            
            outHeader = ["Timestamp", "FixationSeq", "SaccadeSeq"];
            df.to_csv(fullPytrkfn, columns = outHeader, index=False)
            os.remove(tobiifn);
            gotFile = True;
            break;

    print("Extraction of oculomotor events is complete.")

def getOutFileName(inFileBase, ver):

    toks = inFileBase.split('_');
    
    subj = toks[0];
    sess = toks[1];
    difficulty = toks[5];
    runNum = toks[6];

    if (ver == 'pytrk'):
        outFile = subj+'_'+sess+'_ocuevts_'+difficulty+'_'+runNum+'.csv';
    elif (ver == 'tobii'):
        outFile = subj+'_'+sess+'_eyetrk_'+difficulty+'_'+runNum+'_tobii.txt';
    return outFile;

       
def exportToTobiiTXT(dataDict, fnameRoot, outFileDir):

    data_arr_orig = dataDict['data'];
    header = dataDict['header'];
    exportToTobiiTXT_base(data_arr_orig, header, fnameRoot, outFileDir);
    
def exportToTobiiTXT_base(data_arr_orig, header, fnameRoot, outFileDir):
    [tobiiH, tobIdxs, data_arr] = convertHeaderToTobii(header, data_arr_orig);

    [data_arr, timeIdx] = adjustTime(tobiiH, tobIdxs, data_arr);
    data_arr = adjustPupil(tobiiH, tobIdxs, data_arr, "Right");
    data_arr = adjustPupil(tobiiH, tobIdxs, data_arr, "Left");

    [tobiiH, tobIdxs, data_arr] = addGaze2D(tobiiH, tobIdxs, data_arr, "Right");
    [tobiiH, tobIdxs, data_arr] = addGaze2D(tobiiH, tobIdxs, data_arr, "Left");

    da = data_arr.transpose();
    times = da[0];

    tobiiBase = getOutFileName(fnameRoot, 'tobii');
    tobiifn = os.path.join(outFileDir, tobiiBase); 
    outf = open(tobiifn, 'w');
    
    try:

        outf.write('\t'.join(tobiiH)+'\n');

        for row in data_arr:
            row = np.append(row, 0);
            row = np.append(row, 0);
            str_row = list(map(str, row[tobIdxs]));
            toks = str_row[timeIdx].split('.');
            str_row[timeIdx] = toks[0]; #PyTrack needs timestamp to be int (milliseconds). I am converting the Vive seconds with floating point milliseconds to an int of # of milliseconds by multiplying by 1000 in adjustTime().
            outf.write('\t'.join(str_row)+'\n');

        str_row = list(map(str, row[tobIdxs]));
        toks = str_row[timeIdx].split('.');
        str_row[timeIdx] = toks[0];
        for e in range(1, len(row)-3):
            str_row[e] = ""
        outf.write('\t'.join(str_row)+'\n');
        
    finally:
        outf.flush();
        outf.close();

#Vive Pro Eye data is missing the Gaze2D coordinates. PyTrack uses these for saccade and fixation detection. Thus, we calculate them here by projecting the 3D gaze vector onto a 2D plane.
#Gaze2D is in normalized video coordinates. (0,0) corresponds to top left corner of the scene camera video and (1,1) corresponds to the bottom right corner. https://www.tobiipro.com/siteassets/tobii-pro/products/software/tobii-pro-glasses-3-api/tobii-pro-glasses-3-developer-guide.pdf/?v=1.0
def addGaze2D(tobiiH, tobIdxs, data_arr, eyeRorL):
    
    g3i_X = tobiiH.index('Gaze3d_'+eyeRorL+'.x');
    g3i_Y = tobiiH.index('Gaze3d_'+eyeRorL+'.y');
    g3i_Z = tobiiH.index('Gaze3d_'+eyeRorL+'.z');

    g3oi_X = tobIdxs[g3i_X];
    g3oi_Y = tobIdxs[g3i_Y];
    g3oi_Z = tobIdxs[g3i_Z];

    g2x_arr = [];
    g2y_arr = [];

    for d in range(len(data_arr)):
        
        g3xr = data_arr[d, g3oi_X];
        g3yr = data_arr[d, g3oi_Y];
        g3zr = data_arr[d, g3oi_Z];
        
        r = np.sqrt(g3xr*g3xr + g3yr*g3yr + g3zr*g3zr);
        g3x = g3xr/r;
        g3y = g3yr/r;
        g3z = g3zr/r;
        
        theta = np.degrees(np.arctan([g3y/g3x]));
        phi = np.degrees(np.arctan([g3y/g3z]));
    
        if (theta < 0):
            theta = theta + 180;
            
        if (phi < 0):
            phi = phi + 180;

        if (phi > 90):
            phi = phi - 180;

        theta = 1440*((theta - 90)/90);
        phi = 1600*phi/90;

        g2x_arr.append(theta);
        g2y_arr.append(phi);

    g2x_nparr = np.array(g2x_arr)
    g2y_nparr = np.array(g2y_arr)

    data_arr = np.append(data_arr, g2x_nparr, axis=1);
    data_arr = np.append(data_arr, g2y_nparr, axis=1);
    
    tobiiH.append('Gaze2d_'+eyeRorL+'.x');
    tobIdxs.append(max(tobIdxs)+1);

    tobiiH.append('Gaze2d_'+eyeRorL+'.y');
    tobIdxs.append(max(tobIdxs)+1);

    return [tobiiH, tobIdxs, data_arr];

    
def adjustPupil(tobiiH, tobIdxs, data_arr, eyeRorL):

    pupilIdx = tobiiH.index('PupilDiam_'+eyeRorL);
    origIdx = tobIdxs[pupilIdx];
    a = data_arr[:,origIdx];
    data_arr[:,origIdx] = np.where(a == -1, 0, a);

    return data_arr;

def convertTimeMillis2Days(timecol):
    timecol2 = timecol/float(24*3600*1000);

    return timecol2;
    
def adjustTime(tobiiH, tobIdxs, data_arr):
    timeColIdx = tobiiH.index('Recording timestamp');

    da = data_arr.transpose();
    times = da[0];
    
    origIdx = tobIdxs[timeColIdx];

    data_arr[:,origIdx] *= 24*3600*1000;
    dd = data_arr[:,origIdx];
    data_arr[:,origIdx] = dd.astype(float);

    da2 = data_arr.transpose();
    times2 = da2[0];

    return [data_arr, origIdx];


def ndprint(a, format_string ='{0:.20f}'):
    return [format_string.format(v,i) for i,v in enumerate(a)];

#Converts the gaze data into the standard tobii format.
def convertHeaderToTobii(viveH, data_arr_orig):
    #Recording timestamp	Eyetracker timestamp	Eyepos3d_Left.x	Eyepos3d_Left.y	Eyepos3d_Left.z	Eyepos3dRel_Left.x	Eyepos3dRel_Left.y	Eyepos3dRel_Left.z	Gaze2d_Left.x	Gaze2d_Left.y	Gaze3d_Left.x	Gaze3d_Left.y	Gaze3d_Left.z	PupilDiam_Left	Validity_Left	Eyepos3d_Right.x	Eyepos3d_Right.y	Eyepos3d_Right.z	Eyepos3dRel_Right.x	Eyepos3dRel_Right.y	Eyepos3dRel_Right.z	Gaze2d_Right.x	Gaze2d_Right.y	Gaze3d_Right.x	Gaze3d_Right.y	Gaze3d_Right.z	PupilDiam_Right	Validity_Right	Event value	Event message

    tobiiH = [];
    ctr_new = 0;
    ctr_old = 0;
    tobIdxs = [];
    data_arr = np.empty((len(data_arr_orig),0), float); #np.array([]);
    
    for h in viveH:
        if (h == 'time_dn'):
            tobiiH.append('Recording timestamp');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            #da = data_arr.transpose();
            ctr_new = ctr_new + 1;
        
            tobiiH.append('Eyetracker timestamp');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
            
        elif (h == 'validity_l'):
            tobiiH.append('Validity_Left');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'validity_r'):
            tobiiH.append('Validity_Right');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_l_x_mm'):
            tobiiH.append('Eyepos3d_Left.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_l_y_mm'):
            tobiiH.append('Eyepos3d_Left.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_l_z_mm'):
            tobiiH.append('Eyepos3d_Left.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_r_x_mm'):
            tobiiH.append('Eyepos3d_Right.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_r_y_mm'):
            tobiiH.append('Eyepos3d_Right.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_origin_r_z_mm'):
            tobiiH.append('Eyepos3d_Right.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_l_x'):
            tobiiH.append('Gaze3d_Left.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_l_y'):
            tobiiH.append('Gaze3d_Left.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_l_z'):
            tobiiH.append('Gaze3d_Left.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_r_x'):
            tobiiH.append('Gaze3d_Right.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_r_y'):
            tobiiH.append('Gaze3d_Right.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'gaze_direction_r_z'):
            tobiiH.append('Gaze3d_Right.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_diameter_l_mm'):
            tobiiH.append('PupilDiam_Left');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_diameter_r_mm'):
            tobiiH.append('PupilDiam_Right');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_l_x'):
            tobiiH.append('Eyepos3dRel_Left.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_l_y'):
            tobiiH.append('Eyepos3dRel_Left.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_l_z'):
            tobiiH.append('Eyepos3dRel_Left.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_r_x'):
            tobiiH.append('Eyepos3dRel_Right.x');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_r_y'):
            tobiiH.append('Eyepos3dRel_Right.y');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;
        elif (h == 'pupil_position_r_z'):
            tobiiH.append('Eyepos3dRel_Right.z');
            tobIdxs.append(ctr_new);
            data_arr = np.append(data_arr, np.array([list(data_arr_orig[:,ctr_old])]).transpose(), axis=1);
            ctr_new = ctr_new + 1;

        ctr_old = ctr_old + 1;

    tobiiH.append('Event value');
    evCol = np.zeros((data_arr.shape[0], 1)).astype(int);
    evCol[0] = 1; #trial start event 
    evCol[data_arr.shape[0]-1] = 2; #trial end event 
    data_arr = np.append(data_arr, evCol, axis=1);
    tobIdxs.append(len(tobIdxs));
    
    tobiiH.append('Event message');
    emCol = np.zeros((data_arr.shape[0], 1)).astype(int);
    emCol[0] = 1; #trial start event
    emCol[data_arr.shape[0]-1] = 2; #trial end event.
    data_arr = np.append(data_arr, emCol, axis=1);
    
    tobIdxs.append(len(tobIdxs));
    
    return [tobiiH, tobIdxs, data_arr];

if __name__ == '__main__':
    sys.exit(main())

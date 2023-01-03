% Derive the measures of performance for each trial
% The measure of performance include 
% 1) Localizer error (i.e., horizontal deviation from ideal path)
% 2) Glide Slope error (i.e., vertical deviation from expected -3 deg decent)
% 3) Airspeed error (i.e., deviation from the ideal 115 knots)
% Instantaneous error is computed for each of the three components
% A total instantaneous error, sum of the component mangnitudes, is also computed
% Finally, a single cumulative total error is derived for each trial
% Output files are:
% A) File per trial with time series of errors
% B) Summary file across all subjects/trials with cumulative errors
%
% Research was sponsored by the United States Air Force Research Laboratory 
% and the United States Air Force Artificial Intelligence Accelerator and was 
% accomplished under Cooperative Agreement Number FA8750-19-2-1000. 
% The views and conclusions contained in this document are those of the authors 
% and should not be interpreted as representing the official policies, either 
% expressed or implied, of the United States Air Force or the U.S. Government. 
% The U.S. Government is authorized to reproduce and distribute reprints for 
% Government purposes notwithstanding any copyright notation herein.

clear, clc

dpath = 'Z:\cogpilot-LL_shared\dataManuscript\dataPackage\task-ils';
files = dir( fullfile( dpath , '**', '*lslxp11xpcac*.mat') );

trial = nan(length(files),8); % subj, ses, run#, difficulty, gs, loc, airspeed, cume error

isExportPerfCsv = true; % 


for f = 1 : length( files )
    
    fname = files(f).name;
    
    %% parse block and difficulty versions
    subj = extractAfter( fname , 'sub-' );
    subj = str2double( subj(3:5) );
    
    ses  = extractAfter( fname , 'ses-' );
    ses  = str2double( ses(1:8) );

    difficulty = extractAfter( fname , 'level-' );
    difficulty = str2double( difficulty(1:2) );
       
    runID = extractAfter( fname , 'run-' );
    runID = str2double( runID(1:3) );
    
    fprintf('sub-%03d_ses-%i_difficulty-%03d_Run-%03d\n',subj,ses,difficulty,runID)
    
    %% load data and convert to table
    
    % data struct include .data, .header, .info
    data_struct = load( fullfile( files(f).folder , files(f).name ) );
    data        = array2table( data_struct.data , 'VariableNames', data_struct.header );
    
    time = data.time_dn; % in matlab datenum format (i.e., units == days)
    dur  = 24*3600*(time(end) - time(1));  % in seconds to normalize error values for the trials
    
    %% ILS measures of performance
    
    loc = data.aircraft_ils_deflection_h;
    gs  = data.aircraft_ils_deflection_gs;
        
    
    %% Compute the //Localizer// Error
    
    wgs84 = wgs84Ellipsoid; % object representing the Geodetic map
    
    % plotted as longitutde, latitude, elevation (m)
    sitstart = [-71.5843, 42.4976, 1314]; % starting location to enable 3deg descent 
    origin = [-71.2964, 42.4715, 37.4]; % presumed runway ILS location - "origin"
    
	el_err = nan( height(data),1);
    
    for p = 1 : height(data)
        
        currpos = [data.aircraft_longitude_deg(p), data.aircraft_latitude_deg(p), data.aircraft_elevation_m(p)];
        [xEast,yNorth,zUp] = ...
            geodetic2ned(currpos(2),currpos(1),currpos(3), origin(2), origin(1), origin(3), wgs84);
        
        
        % current pos to ILS end
        dist1 = sqrt( xEast.^2 + yNorth.^2 + zUp.^2 ); 
        
        % sin(theta) = opp/hyp; theta = invsin( opp/hyp )
        el_err(p) = asind( zUp / dist1 );
       
    end
    
    %% Compute //Glide Slope// Error
    
    % plotted as longitutde, latitude, elevation (m)
    origin = [-71.26841, 42.46887, 37.4]; % presumed runway ILS location - "origin"
    
    % negate elevation for azimuthal angle calcuation (i.e., origin(3))
    [origEast,origNorth,origUp] = ...
            geodetic2ned(sitstart(2),sitstart(1),origin(3), origin(2), origin(1), origin(3), wgs84);
            
    az_err = nan( height(data),1);
    
    for p = 1 : height(data)
        
        currpos = [data.aircraft_longitude_deg(p), data.aircraft_latitude_deg(p), data.aircraft_elevation_m(p)];
        [xEast,yNorth,zUp] = ...
            geodetic2ned(currpos(2),currpos(1),currpos(3), origin(2), origin(1), origin(3), wgs84);
        
        
        % for the horizontal deviation, take the dot product, but negate the elevation differences
        num = dot( [xEast,yNorth,0] , [origEast, origNorth, 0] );
        den = sqrt( xEast.^2 + yNorth.^2 ) * sqrt( origEast.^2 + origNorth.^2 );
        az_err(p) = acosd( num / den );

    end
    
    
    %% Clean up error signals
    
    el_err = -3.*(el_err+3); % assumed -3deg is ideal
    az_err = az_err .* sign( loc ); % dot products are always positive 
    
    % if subject flies past the runway, the angle approaches 90 deg
    idxFlyPast = data.aircraft_longitude_deg > origin(1);

    el_err( idxFlyPast ) = 3;
    az_err( idxFlyPast ) = 3;
    
    % cap the error at 3 deg
    idxErrorMax = el_err > 3;
    el_err( idxErrorMax ) = 3;
    
    idxErrorMax = el_err < -3;
    el_err( idxErrorMax ) = -3;
    
    idxErrorMax = az_err > 3;
    az_err( idxErrorMax ) = 3;
    
    idxErrorMax = az_err < -3;
    az_err( idxErrorMax ) = -3;
    
        
    %% Compute Airspeed error
    
    spd_err = (data.aircraft_indicated_airspeed_kias - 115)./10; % to put onto the 0 to 3 scale
    spd_err( spd_err > 3 ) = 3;
    spd_err( spd_err < -3 ) = -3;
    
    %% Aggregate metrics of performance for each trial
    
    % only compute errors between start of flight (speed > 0) and before touchdown (AGL > 200' == 60 m)
    % this comes from pilot training doctorine that once "minimums" are reached, the ILS system is not used; just visual landing
    idxUseErr = find( diff(data.aircraft_indicated_airspeed_kias) ~= 0 ,1, 'first' ) : find( data.aircraft_elevation_m-origin(3) > 85, 1, 'last');
    
    trial(f,1:4) = [subj, ses, runID, difficulty];
    trial(f,5:7) = [ sum(abs(el_err(idxUseErr))) , sum(abs(az_err(idxUseErr))) , sum(abs(spd_err(idxUseErr))) ] ;
    trial(f,8)   =  sum(trial(f,5:7));
    
    %% Export to csv
    
    if isExportPerfCsv
        
        perf = table('Size', [length(idxUseErr),5], ...
            'VariableTypes', {'double', 'double', 'double', 'double','double'}, ...
            'VariableNames', {'time_dn', 'glideslope_error_deg', 'localizer_error_deg', 'airspeed_error_kts','total_error'});
        
        perf.time_dn              = time(idxUseErr);
        perf.localizer_error_deg  = roundn( az_err(idxUseErr), -4);
        perf.glideslope_error_deg = roundn( el_err(idxUseErr), -4 );
        perf.airspeed_error_kts   = roundn( spd_err(idxUseErr), -4 );
        perf.total_error          = sum( abs(table2array(perf(:,2:4))) ,2);
        
        
        % save to the same subject/date/run directory
        writetable( perf , ...
        fullfile( files(f).folder , sprintf('sub-cp%03d_ses-%i_task-ils_stream-lslxp11_feat-perfmetric_level-%02dB_run-%03d.csv', subj, ses, difficulty, runID) ) ); 
        
    end
    
    
end % f : files

% for easy visualization, round to 4 decimal places
trial = array2table( roundn(trial,-4), 'VariableNames', ...
    {'subject', 'date', 'run', 'difficulty', 'cumulative_glideslope_error_deg', 'cumulative_localizer_error_deg', 'cumulative_airspeed_error_kts', 'cumulative_total_error'});


writetable( trial , fullfile( dpath , 'PerfMetrics.csv') )

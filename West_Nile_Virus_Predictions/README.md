# Project 4 - Predicting outbreaks caused by West Nile Virus and using cost benefit analysis to help the City of Chicago.

Done by: Richelle-Joy Chia, Er Jie Yong, Meriky Lo

## Introduction

The West Nile Virus (WNV) can be spread to people by the bite of an infected mosquito. The peak period of such occurrence is during summer and fall, with a peak period for disease transmissions from July to September. Currently, WNV is the leading cause of mosquito-borne diseases in the United States (US). Based on statistics, 1 in 5 people experience mild symptoms while 1 in 150 experience severe symptoms. This is worrisome as there are currently no available vaccines.

Chicago is the most poulous city in the State of Illinois and the third most populous city in the US. As such, it is crucial to start taking effective actions to try to contain the massive spread among the public. The City of Chicago has been putting in place some intervention measures to contain the spread, one of which is to spray insecticides using aeroplanes and helicopters to treat large areas.

## Problem Statement

Most often West Nile Virus causes mild, flu-like symptoms. However, in some cases, it can lead to life-threatening illnesses. Here at Disease And Treatment Agency, division of Societal Cures In Epidemiology and New Creative Engineering (DATA-SCIENCE), our goal is to build a model and make predictions that the city of Chicago can use when it decides where to spray pesticides. In order to do this, we engage with past data on the locations where West Nile virus were found with their weather conditions.

### Project Flow and Structure
Please refer to our Project Planning document to retrieve more details on how we worked on the project, a list of our feature engineering, and our modeling structure. 
- https://docs.google.com/spreadsheets/d/1yaMx3A26iPtJak6Bme8B-Hl1aj_j1mi1hd8g64Mq-6g/edit?usp=sharing

## Data description and source

We used the datasets provided by Kaggle, retrieved from https://www.kaggle.com/c/predict-west-nile-virus/
The datasets consist of the following data:
1. train.csv: contains information on locations where mosquitos were trapped, and the presence of virus in them. Data was recorded for years 2007, 2009, 2011, and 2013.
2. test.csv: contains similar information to train data for years 2008, 2010, 2012, 2014.
3. weather.csv: NOAA (National Oceanic and Atmospheric Administration) weather data collected in 2 weather stations between 1 May and 31 Oct from 2007 to 2014.
4. spray.csv: contains date, time and location of pesticide sprays for years 2011 and 2013.
5. Chicago map: openstreetmap data of Chicago

## Feature Engineering
Based on our analysis and research on the culex species of mosquitoes, we performed feature engineering to derive the following additional features
1. Classification of wet vs dry weather
2. Calculation of humidity
3. Identification of traps sprayed within 300ft and 30 days from sprayed location
4. 9 days rolling average of weather data
5. Cumulative count of days since june 1
6. Trap matrix weighted according to distance
7. PDF of west nile virus

## Prediction for WNV - Years 2008, 2010, 2012, 2014
Please refer to our Tableau webpage for more details on our WNV prediction for years 2008, 2010, 2012, and 2014: 
([Link](https://public.tableau.com/app/profile/m.alexander8473/viz/WNV_16660866134960/Story1))
- The specific notebook and files can be found in the Tableau folder.

## Cost Benefit Analysis

In the whole of the USA, total mean cost of WNV hospitalized cases and deaths is approximately $56 million per year (see [Link](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3945683/)). These are big sums and cost to human wellness that can be saved through targeted prevention measures such as insecticide spraying.

According to National Library of Medicine report (see Table 2 in this [Link](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3322011/)), estimated average medical cost for one single case of WNV disease is USD 33,143.
Between 2003 and 2012, the city of Chicago sees an average of 17 cases per year (see [Link](https://www.chicago.gov/content/dam/city/depts/cdph/statistics_and_reports/CDInfo_2013_JULY_WNV.pdf)). 
This means that total cost per year based on this average = USD 563,431.

The most commonly used pesticide in Chicago city is Zenifex E4 (see [Link](https://www.chicago.gov/content/dam/city/depts/cdph/Mosquito-Borne-Diseases/Zenivex.pdf)).

The cost of Zenivex E4 is USD 78.85 per gallon or USD 0.92 per acre ([Link](http://www.centralmosquitocontrol.com/-/media/files/centralmosquitocontrol-na/us/resources-lit%20files/2015%20zenivex%20pricing%20brochure.pdf))

The area of Chicago city is 150,000 acres.

With this information, the cost of spraying can calculated following two scenarios:<br>
(i) spraying the whole Chicago city <br>
(ii) targeted spray only on locations where virus presence is predicted.

(i) if spraying the whole Chicago city
Medical cost arising from WNV is calculated as:<br>
    Total mean medical cost per year based on above calculation is USD 563,431.
    
Pesticides spraying on the whole Chicago city is calculated as
Chicago City Area (acres)       = 150,000
Pesticide cost per acre         =  USD 0.92
Total cost per month            = USD 138,000
Total cost per year (assuming 3 sprays/year) = USD 414,000

Total cost saved is =  USD 149,431(26.5%)

(ii) targeted spraying informed by our model predictions
Our model predicts virus presence for 2014 to be on the following months and number of traps:<br>
July : on 4 traps<br>
August : on 123 traps <br>
September : on 97 traps <br>
October : on 19 traps <br>

Based on this prediction, pesticide spraying can be directed at specific timeframe and specific locations.
Thus, spraying cost can be calculated as:
approximate area per trap    = 150,000/134(total number of traps)
Cost of pesticide in July (spraying on 4 traps) =  USD 4118 <br>
Cost of pesticide in Aug (spraying on 123 traps) =  USD 126626<br>
Cost of pesticide in Sep (spraying on 97 traps) =   USD 99860<br>
Cost of pesticide in Oct (spraying on 19 traps) = USD 19560<br>

Total cost saved for 2014 is USD 313,270 (55.6%).

## Limitations of our cost benefit analysis:

However, these cost benefit calculations comes with a few limitations. Firstly, our analysis did not take into account the costs of manpower for spraying, which may be a hefty sum. Secondly, we assumed that the effectiveness of pesticides is 100%, but this may not be true. Next, we did not account for possible costs that may arrise from lost of productivity due to serious complications and deaths. Finally, human's health cannot be quantified with a price and there may be more than just moeny involved.

## Conclusion:

Overall, from our models, we learned that the most important features are location and date. We have also observed from past data that current spraying is not optimum in reducing number of mosquitoes / virus. This is because the spraying took place after virus was found, and spraying locations do not cover most virus outbreak areas.

## Recommendations:

We would also like to provide a few recommendations. First, we would recommend targeted spraying on specific dates (before mosquitoes were found) and specific locations based on our model predictions. Next, it would be useful to identify more effective pesticides to ensure that we are not wasting resources. Finally, we recommend that the city of Chicago can deploy other preventive measures such as spraying on high risk areas and public education.

## Next Steps:

In future, before spending resources on spraying around the city, it is critical to first predict outbreaks based on timeframe and location, predict number of mosquitos present, and to do more feature engineering/EDA to identify higher correlated features.

## Other references:

1. Illinois Department of Public Health: West Nile Virus. Retrieved from: https://dph.illinois.gov/topics-services/diseases-and-conditions/west-nile-virus.html
2. Peterson et al. (2006) A Human-Health Risk Assessment for West Nile Virus and Insecticides Used in Mosquito Management. Retrieved from: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1392230/
3. Sejvar, J (2003) West Nile Virus: An Historical Review. Retrieved from: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3111838/


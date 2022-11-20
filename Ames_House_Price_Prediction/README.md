<img src="./images/blackfin_logo_white.png" style="float: left; margin: 0 20px 0 20px; height: 120px">

# Ames House Price Prediction

A machine learning model by BlackFin corporation

# Introduction
## Background
With the recent volatile housing market in the US [(source)](https://money.yahoo.com/housing-market-extremely-volatile-with-private-equity-accounting-for-a-third-of-the-sales-expert-152958055.html), alot of home owners are unsure of the valuation of their homes. This resulted in home owners either leaving money on table when transacting below market rate, or pricing it too high and having no sales even though their house has been listed for ages. This problem also affects the rental market as home owners generally use the home value to price the monthly rentals.

## Mission
Blackfin, much like its competitor, [Redfin](https://www.redfin.com/why-redfin), prides itself in being a **data first** real estate company. As the data science team of BlackFin, we set forth to use machine learning to predict the most accurate house prices in the Ames region. This proprietary algorithim will also be released to the public. We expect this model to
1) help home owners to get the most accurate prices on their home
2) which in turn, will encourage home owners to sell the houses to Blackfin
3) Utilising our interior experts to renovate, design and optimise for property listing, we will price the house again using this model and sell it to the market at a markup
4) Estimate renovation, designing budget for blackfin internal team based on expected bought price from home owners and expected sale price in the future

## Problem Statement
To assist both BlackFin and home owners to get the most accurate house prices using historical data

## Scope
Based on the data of house sold between 2006 and 2010, we aim to train a regression model that is highly accurate in predicting home sale prices in the Ames region

## Success Factor
Our model success would be evaluated based on
- How close our predicted model is to the actual sale price (for existing training and testing data)
- How long long does the house stay on the market and how far is our initial price vs the final sale price (for future newly predicted houses)

## Dataset
- [`train.csv`](./datasets/train.csv): Datasets of Ames Housing data between 2006 and 2010 with Saleprice
- [`test.csv`](./datasets/test.csv): Datasets of Ames Housing data without Saleprice

# Methodology
## Data cleaning
- Null numerical data was imputed based on a linear regression method should they adopt a linear trend. These are done for `Lot Frontage` and `Garage Yr Blt`. The rest of the null numerical data are imputed based on its mean as it has less than 1% missing data which should not significantly affect the data's general mean and standard deviation
- Null categorical data remain as null under the assumption that these data was left out due to the house not having the corresponding elements of the house. Example, there would not be any `Pool QC` if there's no pool
- Features that are highly correlated are dropped. These are `Garage Yr Blt`, `Total Bsmt SF`, `TotRms AbvGrd`, `Garage Cars`, `Exterior 2nd`, `Fireplace Qu`, `Garage Qual`, `Pool QC`
- Outliers although identified, are not removed from the modeling as it increases the error of our model

## Modeling
- Modelling was managed under the MLOps methodology and is logged using `MLFlow`
- A baseline model was first established using linear regression. However the result was unsatisfactory. While R2 score for train dataset was high at 94.4%, the R2 score for test data is negative. This indicate an overfitting of the model and feature selection has to be done to reduce variance of our model
- Exploratory modeling was done using `GridSearchCV` and `Pycaret`. The summary of the model are summarised in the table below:

Model | Best Regression | CV R2 result | Kaggle Private Score (RMSE) | Kaggle Public Score (RMSE)
-------- | ---------- | -------- | -------- | -------- 
Baseline model | Linear Regression | -6052502.05 |  415522585.39 | 649729334.37
GridSearchCV | Linear Regression | 0.85 | 26206.55 | 31947.93
Multi Regression GridSearchCV | ElasticNet | 0.87 | 24219.97 | 30202.74
Baseline Pycaret | Gradient Boosting Regressor | 0.91 |  21867.08 | 28079.46
Pycaret w/o outliers | Bayesian Ridge | 0.92 | 22611.63 | 26095.17
**Pycaret w scaling & selection*** | Bayesian Ridge | 0.93 | 17983.57 | 22604.85

*Model was selected as it is the **Top #1** private score on [kaggle](https://www.kaggle.com/competitions/dsi-us-11-project-2-regression-challenge/leaderboard)

## Deployment
The selected model was deployed using the following packages/programs
- Flask
- Docker
- Google Cloud
- Streamlit

The final model is now live on streamlit: [Link](https://erjieyong-pytho-ames-house-price-predictionstreamlit-app-lmrvb2.streamlitapp.com/)

# Conclusion
Based on our analysis, a house's neighborhood is one of the most important features which confirm conventional thinking. Out of all the neighborhoods, `StoneBr` and `NoRidge` will likely get the higher Sale Price.

The other features features which will increase the selling price of the house are as follows
- Excellent exterior material quality
- Brick Face exterior covering on house
- Excellent kitchen quality
- Typical home functionality rating
- Good basement exposure
- Year Built
- Wood Shingles roof material
- Overall Square foot at above ground living area, basement and lot area

While we are unable to change the certain aspects of the house such as the neighborhood and overall square foot. However, this findings also allow us to advise our internal team at BlackFin to concentrate on sprucing up the other features that can be changed, (such as the quality of the exterior, kitchen) to achieve the highest cost efficiency and achieve the best sales price.

For the home owners, these findings would also serve as a guideline on what to focus on in order to improve the selling price of their houses

Most importantly, we are fairly confident in our prediction model as we have a r2 score of 93.2% which means that our model is able to explain 93.2% of the test salesprice. 

# Further Evaluation
- Update house prices to recent years and months so that it more accurately reflect the current market situation
- Perform more feature engineering such as 
    - Total years lived in = year sold - year built
    - Total Interior square footage = TotalBsmtSF + GrLivArea + GarageArea
    - Total Exterior square footage = LotArea + MasVnrArea + WoodDeckSF + OpenPorchSF + EnclosedPorch + 3SsnPorch + ScreenPorch + PoolArea
    - combination of numerical * categorical features
- Take into account macro economic factors to more accurately predict house prices such as
    - federal interest rate
    - gdp
    - unemployment rate
- Further beautify the streamlit app to include more comments in the help section
    
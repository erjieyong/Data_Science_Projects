from flask import Flask, request 
import pandas as pd 
import os 
import mlflow.pyfunc


api = Flask('ModelEndpoint')

model = mlflow.pyfunc.load_model(model_uri="./model")

@api.route('/') 
def home(): 
    return {"message": "Hello!", "success": True}, 200

@api.route('/predict', methods = ['POST']) 
def make_predictions():
    user_input = request.get_json(force=True) 
    df_schema = {'MS SubClass':str,
                 'MS Zoning' : str,
                 'Street' : str,
                 'Alley' : str,
                 'Lot Shape' : str,
                 'Land Contour' : str,
                 'Utilities' : str,
                 'Lot Config' : str,
                 'Land Slope' : str,
                 'Neighborhood' : str,
                 'Condition 1' : str,
                 'Condition 2' : str,
                 'Bldg Type' : str,
                 'House Style' : str,
                 'Roof Style' : str,
                 'Roof Matl' : str,
                 'Exterior 1st' : str,
                 'Exterior 2nd' : str,
                 'Mas Vnr Type' : str,
                 'Exter Qual' : str,
                 'Exter Cond' : str,
                 'Foundation' : str,
                 'Bsmt Qual' : str,
                 'Bsmt Cond' : str,
                 'Bsmt Exposure' : str,
                 'BsmtFin Type 1' : str,
                 'BsmtFin Type 2' : str,
                 'Heating' : str,
                 'Heating QC' : str,
                 'Central Air' : str,
                 'Electrical' : str,
                 'Kitchen Qual' : str,
                 'Functional' : str,
                 'Fireplace Qu' : str,
                 'Garage Type' : str,
                 'Garage Finish' : str,
                 'Garage Qual' : str,
                 'Garage Cond' : str,
                 'Paved Drive' : str,
                 'Pool QC' : str,
                 'Fence' : str,
                 'Misc Feature' : str,
                 'Sale Type' : str,
                 'Lot Frontage' : float,
                 'Lot Area' : float,
                 'Overall Qual' : float,
                 'Overall Cond' : float,
                 'Year Built' : float,
                 'Year Remod/Add' : float,
                 'Mas Vnr Area' : float,
                 'BsmtFin SF 1' : float,
                 'BsmtFin SF 2' : float,
                 'Bsmt Unf SF' : float,
                 'Total Bsmt SF' : float,
                 '1st Flr SF' : float,
                 '2nd Flr SF' : float,
                 'Low Qual Fin SF' : float,
                 'Gr Liv Area' : float,
                 'Bsmt Full Bath' : float,
                 'Bsmt Half Bath' : float,
                 'Full Bath' : float,
                 'Half Bath' : float,
                 'Bedroom AbvGr' : float,
                 'Kitchen AbvGr' : float,
                 'TotRms AbvGrd' : float,
                 'Fireplaces' : float,
                 'Garage Yr Blt' : float,
                 'Garage Cars' : float,
                 'Garage Area' : float,
                 'Wood Deck SF' : float,
                 'Open Porch SF' : float,
                 'Enclosed Porch' : float,
                 '3Ssn Porch' : float,
                 'Screen Porch' : float,
                 'Pool Area' : float,
                 'Misc Val' : float,
                 'Mo Sold' : float,
                 'Yr Sold' : float} # To ensure the feature columns for modeling get the correct datatype, because when Pandas converts from JSON to df, it infers dtype of every col
    user_input_df = pd.read_json(user_input, lines=True, dtype=df_schema) 
    predictions = model.predict(user_input_df).tolist()
    
    return {'predictions': predictions} 
    
if __name__ == '__main__': 
    api.run(host='0.0.0.0', 
            debug=True, 
            port=int(os.environ.get("PORT", 8080))
           ) 

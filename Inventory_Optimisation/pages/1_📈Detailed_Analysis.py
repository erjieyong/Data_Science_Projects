import streamlit as st
import pandas as pd
import scipy.stats as stats
import plotly.express as px
from datetime import datetime
import pydeck as pdk
import numpy as np

#########################
## STREAMLIT STRUCTURE ##
#########################

st.set_page_config(layout="wide")

# Title of the page
st.title("Safety stock, EOQ, ROP Recommender")
st.write("Recommend safety stock, economic order quantity (EOQ), reorder point (ROP) based on established supply chain algorithm. Assumptions made that demand and lead time are independent variables")

# Create placement containers in sequence
stats_col1, stats_col2, stats_col3 = st.columns(3)


###############
## FUNCTIONS ##
###############

average_days_per_month = 30.437

# we need the following so that streamlit will only run the following once
# in this case, it will cache our df and not rerun it everytime we change something on the app
# https://discuss.streamlit.io/t/not-to-run-entire-script-when-a-widget-value-is-changed/502/5
@st.experimental_memo
def read_df_combined():
    df_combined = pd.read_csv('https://generalassemblydsi32.s3.ap-southeast-1.amazonaws.com/ABC_Analysis-221125/df_combined_sanitised.csv')
    # df_combined = pd.read_csv("df_combined.csv")
    df_combined["stock_month_2dp"] = df_combined["stock_month"].round(2)
    df_combined["stock_days_2dp"] = (df_combined["stock_month"]*average_days_per_month).round(2)
    df_combined["current_stock_formatted"] = df_combined["current_stock"].apply(lambda d: f"{int(d):,}")
    df_combined["avg_shipped_qty_2dp"] = df_combined["avg_shipped_qty"].round(2)
    st.session_state.df = df_combined
    return df_combined



if "df" not in st.session_state:
    st.session_state.df = read_df_combined()

   
# Function to get and display preset values in data_form based on historical data
def preset(hub, sku, mode):
    try:
        target_row_no = st.session_state.df[(st.session_state.df['hub']==st.session_state.hub) & (st.session_state.df['sku'] == st.session_state.sku) & (st.session_state.df['mode'] == st.session_state.mode)].index[0]
        
        preset_service_level = st.session_state.df.loc[target_row_no, 'service_level']*100
        preset_demand_mean = st.session_state.df.loc[target_row_no, 'avg_shipped_qty']
        preset_demand_sd = st.session_state.df.loc[target_row_no, 'sd_shipped_qty']
        preset_leadtime_mean = st.session_state.df.loc[target_row_no, 'leadtime_days']
        preset_leadtime_sd = st.session_state.df.loc[target_row_no, 'leadtime_days_sd']
        preset_holding_cost_per_unit_per_month = st.session_state.df.loc[target_row_no, 'holding_cost_per_unit_year']/12
        preset_handling_cost = st.session_state.df.loc[target_row_no, 'handling_cost']
        preset_today_inventory = st.session_state.df.loc[target_row_no, 'current_stock']


        st.session_state.service_level = preset_service_level
        st.session_state.demand_mean = round(preset_demand_mean,2)
        st.session_state.demand_sd = round(preset_demand_sd,2)
        st.session_state.leadtime_mean = round(preset_leadtime_mean,2)
        st.session_state.leadtime_sd = round(preset_leadtime_sd,2)
        st.session_state.holding_cost_per_unit_per_month = round(preset_holding_cost_per_unit_per_month,2)
        st.session_state.handling_cost = round(preset_handling_cost,2)
        st.session_state.today_inventory = round(preset_today_inventory,2)

        st.session_state.preset = True

        safety_stock = st.session_state.df.loc[target_row_no, 'safety_stock']
        eoq = st.session_state.df.loc[target_row_no, 'eoq']
        rop = st.session_state.df.loc[target_row_no, 'rop']
        # display result in 3 col metrics
        result_col1.metric("Safety Stock", f"{safety_stock:,}")
        result_col2.metric("Economic Order Quantiy", f"{eoq:,}")
        result_col3.metric("Reorder Point", f"{rop:,}")

        # Display re-order date
        with result_container:
            # get target row for the chosen SKU and transport mode in CONSOLE HUB
            target_row_no_console = st.session_state.df[(st.session_state.df['hub']=="CONSOLE") & (st.session_state.df['sku'] == sku) & (st.session_state.df['mode'] == mode)].index[0]
            console_support = st.session_state.df.loc[target_row_no_console, "console_support"]
            if np.isnan(console_support):
                st.markdown(f"""
                <div style="background-color:rgba(250, 202, 43, 0.2);padding:16px;color:rgb(148, 124, 45);border-radius:2%;margin:1rem 0 1rem 0">
                Next re-order date: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "rop_date"]}</span><br>
                Recommended Transport Mode: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "recommended_mode"]}</span>
                <br><br>
                Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no_console, "current_stock"]:,} <br>
                Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no_console, "expected_pull_next_90d"]:,} 
                <br><br>
                <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
                </div>
                """, unsafe_allow_html=True)
            elif console_support == False:
                st.markdown(f"""
                <div style="background-color:rgba(255, 43, 43, 0.09);padding:16px;color:rgb(125, 53, 59);border-radius:2%;margin:1rem 0 1rem 0">
                Next re-order date: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "rop_date"]}</span><br>
                CONSOLE Hub support within next 90 days for this SKU in all hubs: <span style = "font-weight: 800;">NO 🚨</span><br>
                Recommended Transport Mode: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "recommended_mode"]}</span>
                <br><br>
                Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no_console, "current_stock"]:,} <br>
                Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no_console, "expected_pull_next_90d"]:,} 
                <br><br>
                <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
                </div>
                """, unsafe_allow_html=True)
            elif console_support == True:
                st.markdown(f"""
                <div style="background-color:rgba(33, 195, 84, 0.1);padding:16px;color:rgb(23, 114, 51);border-radius:2%;margin:1rem 0 1rem 0">
                Next re-order date: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "rop_date"]}</span> <br>
                CONSOLE Hub support within next 90 days for this SKU in all hubs: <span style = "font-weight: 800;">YES ✅</span><br>
                Recommended Transport Mode: <span style = "font-weight: 800;">{st.session_state.df.loc[target_row_no, "recommended_mode"]}</span>
                <br><br>
                Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no_console, "current_stock"]:,} <br>
                Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no_console, "expected_pull_next_90d"]:,} 
                <br><br>
                <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
                </div>
                """, unsafe_allow_html=True)

        # display warning if rop is higher than eoq
        if rop > eoq:
            result_container.info("SERANGOONce EOQ is less than ROP due to low handling cost, demand or holding cost, we will plot the inventory level assuming that we order in multiple of EOQ until it exceed ROP. In actual situation, combine them with other skus to yield much better overall costs")

        # calculate inventory level over 365 days
        data = calc_365_inventory(safety_stock, eoq, rop, st.session_state.demand_mean, st.session_state.demand_sd, st.session_state.leadtime_mean, st.session_state.leadtime_sd, random_demand_leadtime_boolean = False)

        # display matplotlib chart based on data    
        fig = px.line(data, x="day", y="inventory", title='Inventory levels over a year', labels={"day":"Number of days in a year", "inventory": "Inventory Level"})
        fig.add_hline(y=rop, line_dash="dash", line_color="orange", annotation_text="reorder point")
        fig.add_hline(y=safety_stock, line_dash="dash", line_color="green", annotation_text="safety stock")
        result_container.plotly_chart(fig, theme = 'streamlit')

    except:
        preset_form.write(f"This SKU is not a cat b item at {st.session_state.hub}.  \n **NO PRESET LOADED**")

# Function to return nan, false or true
# for use when determine whether console can support based on expected pull in next 90 days
def pos_neg_nan(val):
  if np.isnan(val):
    return np.nan
  elif val > 0:
    return True
  elif val <= 0:
    return False

# Calculate the expected total pull from console hub from all hubs, specific sku and mode
# and evaluate if console hub can support the expected pull
def console_support():
    date_90days_later = pd.to_datetime('today').normalize() + pd.Timedelta(days=90)
    df_expected_pull = st.session_state.df[["sku", "mode", "actual_eoq"]][(st.session_state.df["hub"]!="CONSOLE") & (pd.to_datetime(st.session_state.df["rop_date"], format=r"%Y-%m-%d") < date_90days_later)].groupby(["sku", "mode"]).sum("actual_eoq").reset_index()
    df_expected_pull.columns = ["sku","mode","expected_pull_next_90d"]
    st.session_state.df.drop(["expected_pull_next_90d","console_support"], axis = 1, inplace = True)
    st.session_state.df = st.session_state.df.merge(df_expected_pull, how="left", on=["sku","mode"])

    st.session_state.df["console_support"] = st.session_state.df["current_stock"] - st.session_state.df["expected_pull_next_90d"]
    st.session_state.df["console_support"] = st.session_state.df["console_support"].apply(pos_neg_nan)

    st.session_state.df = st.session_state.df

def recommend_transport_mode(hub, sku, df):
  target_rows = df[["hub","sku","mode","handling_cost", "leadtime_days", 'days_to_rop']][(df["hub"]==hub)&(df["sku"]==sku)].index
  # if any of the days_to_rop is more than 0, we will take the one that is the lowest handling cost
  if any(df.loc[target_rows, "days_to_rop"]>0):
    print("inside recommend_transport_mode func, some are more than 0")
    temp_df = df[["mode","handling_cost"]][(df["hub"]==hub)&(df["sku"]==sku)&(df["days_to_rop"]>0)]
    recommended_mode = temp_df["mode"][temp_df["handling_cost"] == temp_df["handling_cost"].min()].iloc[0]

  # if all the days_to_rop is 0, it means we are already behind time, hence, we take the fastest leadtime, ignoring cost
  elif all(df.loc[target_rows, "days_to_rop"]) == 0:
    print("inside recommend_transport_mode func, All 0")
    temp_df = df[["mode","leadtime_days"]][(df["hub"]==hub)&(df["sku"]==sku)&(df["leadtime_days"]>0)]
    recommended_mode = temp_df["mode"][temp_df["leadtime_days"] == temp_df["leadtime_days"].min()].iloc[0]
  return recommended_mode


# Function to calculate SS, EOQ, ROP
def recommender(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost, inventory, hub , sku, mode):
    st.session_state.df = st.session_state.df
    # calculate safety stock
    # assume that demand and leadtime are independent
    z_score = stats.norm.ppf(service_level/100)
    safety_stock = z_score * ((demand_mean * (leadtime_sd/average_days_per_month))**2 + ((leadtime_mean/average_days_per_month) * demand_sd**2))**0.5
    safety_stock = round(safety_stock, 0)

    # calculate economic order quantity
    # (we look at it in a yearly time period because we may only order every few months. Hence, holding cost is on a yearly basis)
    eoq = ((2*handling_cost*demand_mean*12)/(holding_cost_per_unit_per_month*12))**0.5
    eoq = round(eoq, 0)

    # calculate reorder point
    rop = safety_stock + demand_mean * (leadtime_mean / average_days_per_month)
    rop = round(rop, 0)

    # calculate ROP date
    days_to_rop = max((inventory - rop) / (demand_mean / average_days_per_month),0)
    rop_date = (pd.to_datetime('today').normalize() + pd.Timedelta(days=int(days_to_rop))).date()

    # update these calculated values to the df so that it can be downloaded later
    target_row_no = st.session_state.df[(st.session_state.df['hub']==hub) & (st.session_state.df['sku'] == sku) & (st.session_state.df['mode'] == mode)].index[0]

    if st.session_state.preset:
        print("save")
        st.session_state.df.loc[target_row_no, "service_level"] = service_level/100
        st.session_state.df.loc[target_row_no, "avg_shipped_qty"] = demand_mean
        st.session_state.df.loc[target_row_no, "sd_shipped_qty"] = demand_sd
        st.session_state.df.loc[target_row_no, "leadtime_days"] = leadtime_mean
        st.session_state.df.loc[target_row_no, "leadtime_days_sd"] = leadtime_sd
        st.session_state.df.loc[target_row_no, "holding_cost_per_unit_year"] = holding_cost_per_unit_per_month * 12
        st.session_state.df.loc[target_row_no, "handling_cost"] = handling_cost
        st.session_state.df.loc[target_row_no, "safety_stock"] = safety_stock
        st.session_state.df.loc[target_row_no, "eoq"] = eoq
        st.session_state.df.loc[target_row_no, "rop"] = rop
        st.session_state.df.loc[target_row_no, "days_to_rop"] = days_to_rop
        st.session_state.df.loc[target_row_no, "rop_date"] = rop_date


    # calculate recommended transport mode
    # we have to calculate this after rop dates are updated
    recommended_mode = recommend_transport_mode(st.session_state.hub, st.session_state.sku, st.session_state.df)
    print(recommended_mode)
    
    if st.session_state.preset:
        # we don't use target_row_no as we do not need the mode
        st.session_state.df.loc[st.session_state.df[(st.session_state.df["hub"]==hub)&(st.session_state.df["sku"]==sku)].index, "recommended_mode"] = recommended_mode


        # recalculate expected pull and whether console hub can support
        console_support()

    return safety_stock, eoq, rop, rop_date, recommended_mode

# function to calculate the stock level per day taking into consideration all the variables
def calc_365_inventory(safety_stock, eoq, rop, demand_mean, demand_sd, leadtime_mean, leadtime_sd, random_demand_leadtime_boolean):
    safety_stock = round(safety_stock,0)
    eoq = round(eoq,0)
    rop = round(rop,0)
    # we do the following in case rop is higher than eoq. if that happens, then we order multiple times of eoq
    actual_eoq = eoq * np.ceil(rop/eoq)
    demand_per_day = demand_mean / average_days_per_month
    demand_sd_per_day = demand_mean / average_days_per_month

    data = {'day':[], 'inventory':[], 'order':None}
    for day in range(365):
        # track day count
        data['day'].append(day)
        
        # if day 0, assume we have eoq inventory on hand
        if day == 0:
            data['inventory'].append(actual_eoq)
        else:
            # randomised demand based on normal distribution and defined mean and standarad deviation
            if random_demand_leadtime_boolean:
                randomised_demand = round(stats.norm(loc=demand_per_day,scale=demand_sd_per_day).rvs(size=1)[0],0)
            else:
                randomised_demand = demand_per_day
            # deduct inventory per day based on demand
            data['inventory'].append(data['inventory'][-1]-randomised_demand)

            # check if stock after deduct demand is lower than rop. If yes, then raise order
            if data['inventory'][-1] < rop and data['order'] == None:
                # randomised demand based on normal distribution and defined mean and standarad deviation
                if random_demand_leadtime_boolean:
                    randomised_leadtime = round(stats.norm(loc=leadtime_mean,scale=leadtime_sd).rvs(size=1)[0],0)
                else:
                    randomised_leadtime = leadtime_mean
                # deduct inventory per day based on demand
                data['order'] = randomised_leadtime
            elif data['inventory'][-1] < rop and data['order'] > 0:
                data['order'] -= 1
            elif data['inventory'][-1] < rop and data['order'] == 0:
                data['order'] = None
                data['inventory'][day] += actual_eoq
    return data

# Function to change the result output upon presSERANGOONg submit button
def display_recommendations():
    # we have to do this rather than pasSERANGOONg it to the function uSERANGOONg arg because streamlit only update the args after 1 pass
    # to get the most updated value immediately, we need to use session state instead
    service_level = st.session_state.service_level
    demand_mean = st.session_state.demand_mean
    demand_sd = st.session_state.demand_sd
    leadtime_mean = st.session_state.leadtime_mean
    leadtime_sd = st.session_state.leadtime_sd
    holding_cost_per_unit_per_month = st.session_state.holding_cost_per_unit_per_month
    handling_cost = st.session_state.handling_cost
    random_demand_leadtime_boolean = st.session_state.random_demand_leadtime
    inventory = st.session_state.today_inventory
    hub  = st.session_state.hub
    sku = st.session_state.sku
    mode = st.session_state.mode
    
    # Run recommender function
    safety_stock, eoq, rop, rop_date, recommended_mode = recommender(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost, inventory, hub , sku, mode)


    # display result in 3 col metrics
    result_col1.metric("Safety Stock", f"{safety_stock:,}")
    result_col2.metric("Economic Order Quantiy", f"{eoq:,}")
    result_col3.metric("Reorder Point", f"{rop:,}")

    # Display re-order date
    with result_container:
        # get target row for the chosen SKU and transport mode in CONSOLE HUB
        target_row_no = st.session_state.df[(st.session_state.df['hub']=="CONSOLE") & (st.session_state.df['sku'] == sku) & (st.session_state.df['mode'] == mode)].index[0]
        console_support = st.session_state.df.loc[target_row_no, "console_support"]
        if np.isnan(console_support):
            st.markdown(f"""
            <div style="background-color:rgba(250, 202, 43, 0.2);padding:16px;color:rgb(148, 124, 45);border-radius:2%;margin:1rem 0 1rem 0">
            Next re-order date: <span style = "font-weight: 800;">{rop_date}</span><br>
            Recommended Transport Mode: <span style = "font-weight: 800;">{recommended_mode}</span>
            <br><br>
            Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no, "current_stock"]:,} <br>
            Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no, "expected_pull_next_90d"]:,} 
            <br><br>
            <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
            </div>
            """, unsafe_allow_html=True)
        elif console_support == False:
            st.markdown(f"""
            <div style="background-color:rgba(255, 43, 43, 0.09);padding:16px;color:rgb(125, 53, 59);border-radius:2%;margin:1rem 0 1rem 0">
            Next re-order date: <span style = "font-weight: 800;">{rop_date}</span><br>
            CONSOLE Hub support within next 90 days for this SKU in all hubs: <span style = "font-weight: 800;">NO 🚨</span><br>
            Recommended Transport Mode: <span style = "font-weight: 800;">{recommended_mode}</span>
            <br><br>
            Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no, "current_stock"]:,} <br>
            Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no, "expected_pull_next_90d"]:,} 
            <br><br>
            <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
            </div>
            """, unsafe_allow_html=True)
        elif console_support == True:
            st.markdown(f"""
            <div style="background-color:rgba(33, 195, 84, 0.1);padding:16px;color:rgb(23, 114, 51);border-radius:2%;margin:1rem 0 1rem 0">
            Next re-order date: <span style = "font-weight: 800;">{rop_date}</span> <br>
            CONSOLE Hub support within next 90 days for this SKU in all hubs: <span style = "font-weight: 800;">YES ✅</span><br>
            Recommended Transport Mode: <span style = "font-weight: 800;">{recommended_mode}</span>
            <br><br>
            Current stock in CONSOLE Hub: {st.session_state.df.loc[target_row_no, "current_stock"]:,} <br>
            Expected total pull quantity from CONSOLE Hub within next 90 days: {st.session_state.df.loc[target_row_no, "expected_pull_next_90d"]:,} 
            <br><br>
            <font size = "2">* Calculation is based on monthly actual demand (constantly refresh uSERANGOONg shipment order detail report) & transit time (transport mode) assuming that all hubs will use the selected transport mode</font>
            </div>
            """, unsafe_allow_html=True)

    # display warning if rop is higher than eoq
    if rop > eoq:
        result_container.info("SERANGOONce EOQ is less than ROP due to low handling cost, demand or holding cost, we will plot the inventory level assuming that we order in multiple of EOQ until it exceed ROP. In actual situation, combine them with other skus to yield much better overall costs")

    # calculate inventory level over 365 days
    data = calc_365_inventory(safety_stock, eoq, rop, demand_mean, demand_sd, leadtime_mean, leadtime_sd, random_demand_leadtime_boolean)

    # display matplotlib chart based on data    
    fig = px.line(data, x="day", y="inventory", title='Inventory levels over a year', labels={"day":"Number of days in a year", "inventory": "Inventory Level"})
    fig.add_hline(y=rop, line_dash="dash", line_color="orange", annotation_text="reorder point")
    fig.add_hline(y=safety_stock, line_dash="dash", line_color="green", annotation_text="safety stock")
    result_container.plotly_chart(fig, theme = 'streamlit')

###############
## STREAMLIT ##
###############

# Create placement containers in sequence
with st.sidebar:
    st.subheader("Preset values based on historical data")
    # Preset Form
    hub_val = st.selectbox('Hub', sorted(st.session_state.df['hub'].unique()), key='hub')
    sku_val = st.selectbox('SKU', sorted(st.session_state.df['sku'][(st.session_state.df["hub"]==hub_val)].unique()), key='sku')
    mode_val = st.selectbox('Transport Mode', sorted(st.session_state.df['mode'][(st.session_state.df["hub"]==hub_val)&(st.session_state.df["sku"]==sku_val)].unique()), help ="Mode selected would be the same for all hubs and chosen SKU. This would also affect the expected demand from console hub within the next 90 days", key='mode')
    preset_submit = st.button(label='Get Preset', on_click=preset, args = (hub_val, sku_val, mode_val))

    
    download_df = st.session_state.df[['hub','sku','mode','current_stock', 'service_level', 'avg_shipped_qty', 'sd_shipped_qty', 'leadtime_days', 'leadtime_days_sd', 'holding_cost_per_unit_year', 'handling_cost','safety_stock','eoq','actual_eoq','rop', 'rop_date', 'expected_pull_next_90d', 'console_support']].copy()
    download_df.columns = ['hub','sku','mode','current_stock','service_level', 'demand_mean', 'demand_sd', 'leadtime_days', 'leadtime_sd', 'holding_cost_per_unit_year', 'handling_cost_per_order','safety_stock','economic_order_qty','adjusted_economic_order_qty','reorder_point', 'reorder_date', 'expected_pull_next_90d', 'console_support']
    download_csv = download_df.to_csv().encode('utf-8')
    st.download_button('Download Historical Data with calculated SS, EOQ, ROP', data = download_csv, file_name = 'download_csv.csv', mime='text/csv')


# Important statistics
if "today_inventory" not in st.session_state:
    st.session_state.today_inventory = 0
    st.session_state.preset = False
    stats_col1.metric("Today's Inventory", 0)
    stats_col2.metric("Average Demand / Mnth", 0)
    stats_col3.metric("Stock Month", 0)
else:
    target_row_no = st.session_state.df[(st.session_state.df['hub']==st.session_state.hub) & (st.session_state.df['sku'] == st.session_state.sku) & (st.session_state.df['mode'] == st.session_state.mode)].index[0]
    stats_col1.metric("Today's Inventory", f"{st.session_state.df.loc[target_row_no, 'current_stock']:,}")
    stats_col2.metric("Average Demand / Mnth", f"{round(st.session_state.df.loc[target_row_no, 'avg_shipped_qty'],2):,}")
    stats_col3.metric("Stock Month", f"{round(st.session_state.df.loc[target_row_no, 'current_stock']/st.session_state.df.loc[target_row_no, 'avg_shipped_qty'], 2):,}")

# display inventory across all hubs
try:
    with st.expander("Expand to see inventory across all hubs", expanded=False):
        # Display Inventory Map across hub
        st.subheader("Stock months across all hubs")
        layer = pdk.Layer(
            "ColumnLayer",
            data=st.session_state.df[["hub","current_stock_formatted","stock_month_2dp","lat", "lng", "color"]][(st.session_state.df['sku'] == st.session_state.sku) & (st.session_state.df['mode'] == "Air")],
            get_position="[lng, lat]",
            auto_highlight=True,
            get_elevation="stock_month_2dp",
            elevation_scale=200_000,
            radius=200_000,
            pickable=True,
            # elevation_range=[0, 100],
            extruded=True,
            coverage=1,
            # get_fill_color=[255, 165, 0, 100]
            get_fill_color=["255", "165 + color", "0", 100]
        )
        # Set the viewport location
        view_state = pdk.ViewState(
            longitude=0.0, latitude=10.2323, zoom=1, min_zoom=1, max_zoom=15, pitch=45, bearing=0
        )
        # Combined all of it and render a viewport
        r = pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": 
            """<b>Hub:</b> {hub} <br>
            <b>Stock Month:</b> {stock_month_2dp} <br>
            <b>Stock Level:</b> {current_stock_formatted} <br>
            """,
            "style": {"color": "white"}},
        )
        st.pydeck_chart(r)
except:
    pass


with st.expander("Expand to see how demand and leadtime affect SS, EOQ, ROP", expanded=False):
    data_form = st.form(key="data_form")
    data_form.write("*Input the variables in the form below and click submit to derive the recommendation*")
    # data_form.write("*Please note that tweaking these variables are only to simulate how different factors will affect the recommendation. These tweaks will not affect the actual reorder date*")
    data_form_no_col = data_form.columns(1)
    data_form_col1, data_form_col2 = data_form.columns(2)

result_container = st.container()
with result_container:
    result_col1, result_col2, result_col3 = st.columns(3)



# Data Form
service_level_val = data_form.slider('Desired service level for SKU (%)', 1, 100, 90, help="Higher service level will result in higher safety stock", key='service_level')
demand_mean_val = data_form_col1.number_input('Average monthly demand for SKU at hub', value = 12.0, min_value = 0.01, step = 1.0, format = "%f", help="Higher demand will result in higher safety stock, economic order quantity and reorder point", key='demand_mean')
demand_sd_val = data_form_col1.number_input('Standard deviation of monthly demand for SKU at hub', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher variability of demand month on month will result in higher safety stock", key='demand_sd')
leadtime_mean_val = data_form_col2.number_input('Average lead time from SERANGOON to hub (days)', value = 1.0, min_value = 0.01, step = 1.0, format = "%f", help="Longer lead time will result in higher safety stock and reorder point", key='leadtime_mean')
leadtime_sd_val = data_form_col2.number_input('Standard deviation of lead time from SERANGOON to hub (days)', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher variability of lead time will result in higher safety stock", key='leadtime_sd')
holding_cost_per_unit_per_month_val = data_form_col1.number_input('Holding cost per unit of SKU per month', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher holding cost will reduce the economic order quantity per order", key='holding_cost_per_unit_per_month')
handling_cost_val = data_form_col2.number_input('Handling cost per shipment order', value = 1.0, min_value = 0.01, step = 1.0, format = "%f", help="Higher handling cost per order will increase the economic order quantity per order", key='handling_cost')
random_demand_leadtime_boolean = data_form.checkbox("Simulate normalised random demand and leadtime", value=False, key='random_demand_leadtime', help="Enabling this will assuming randomised demand and leadtime normalised according to mean and standard deviation input")
data_submit = data_form.form_submit_button(label = "Submit", on_click = display_recommendations, args=())

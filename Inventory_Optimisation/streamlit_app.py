import streamlit as st
import pandas as pd
import scipy.stats as stats
import plotly.express as px
import math

average_days_per_month = 30.437

df_combined = pd.read_csv('https://generalassemblydsi32.s3.ap-southeast-1.amazonaws.com/df_combined.csv')

# Title of the page
st.title("Safety stock, EOQ, ROP Recommender")
st.write("Recommend safety stock, economic order quantity (EOQ), reorder point (ROP) based on established supply chain algorithm. Assumptions made that demand and lead time are independent variables")




# Create placement containers in sequence
with st.sidebar:
    st.subheader("Preset values based on historical data [OPTIONAL]")
    preset_form = st.form(key="preset_form")

    # download function for historical data
    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    download_df = df_combined[['hub','sku','mode','service_level', 'avg_shipped_qty', 'sd_shipped_qty', '2leg+hub_days', '2leg+hub_days_sd', 'holding_cost_per_unit_year', '2leg+hub_cost','safety_stock','eoq','rop']]
    download_df.columns = ['hub','sku','mode','service_level', 'demand_mean', 'demand_sd', 'leadtime_days', 'leadtime_sd', 'holding_cost_per_unit_year', 'handling_cost_per_order','safety_stock','economic_order_qty','reorder_point']
    download_csv = convert_df(download_df)  
    st.download_button('Download Historical Data with calculated SS, EOQ, ROP', data = download_csv, file_name = 'download_csv.csv', mime='text/csv')


data_container = st.container()
with data_container:
    data_form = st.form(key="data_form")
    data_form.write("*Input the variables in the form below and click submit to derive the recommendation*")
    data_form_no_col = data_form.columns(1)
    data_form_col1, data_form_col2 = data_form.columns(2)

result_container = st.container()
with result_container:
    result_col1, result_col2, result_col3 = st.columns(3)


# Function to get and display preset values based on historical data
def preset(hub, sku, mode):
    try:
        preset_service_level = df_combined['service_level'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]*100
        preset_demand_mean = df_combined['avg_shipped_qty'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]
        preset_demand_sd = df_combined['sd_shipped_qty'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]
        preset_leadtime_mean = df_combined['2leg+hub_days'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]
        preset_leadtime_sd = df_combined['2leg+hub_days_sd'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]
        preset_holding_cost_per_unit_per_month = df_combined['holding_cost_per_unit_year'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]/12
        preset_handling_cost = df_combined['2leg+hub_cost'][(df_combined['hub']==st.session_state.hub) & (df_combined['sku'] == st.session_state.sku) & (df_combined['mode'] == st.session_state.mode)].iloc[0]
        
        if st.session_state.service_level != 90:
            st.session_state.service_level = preset_service_level
        st.session_state.demand_mean = round(preset_demand_mean,2)
        st.session_state.demand_sd = round(preset_demand_sd,2)
        st.session_state.leadtime_mean = round(preset_leadtime_mean,2)
        st.session_state.leadtime_sd = round(preset_leadtime_sd,2)
        st.session_state.holding_cost_per_unit_per_month = round(preset_holding_cost_per_unit_per_month,2)
        st.session_state.handling_cost = round(preset_handling_cost,2)
    except:
        preset_form.write(f"This SKU is not a cat b item at {st.session_state.hub}.  \n **NO PRESET LOADED**")
               
# Function to calculate SS, EOQ, ROP
def recommender(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost):
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

    return safety_stock, eoq, rop

def calc_365_inventory(safety_stock, eoq, rop, demand_mean, demand_sd, leadtime_mean, leadtime_sd, random_demand_leadtime_boolean):
    safety_stock = round(safety_stock,0)
    eoq = round(eoq,0)
    rop = round(rop,0)
    # we do the following in case rop is higher than eoq. if that happens, then we order multiple times of eoq
    actual_eoq = eoq * math.ceil(rop/eoq)
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

def display_recommendations(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost, random_demand_leadtime_boolean):
    # Run recommender function
    safety_stock, eoq, rop = recommender(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost)
    # display result in 3 col metrics
    result_col1.metric("Safety Stock", f"{safety_stock:,}")
    result_col2.metric("Economic Order Quantiy", f"{eoq:,}")
    result_col3.metric("Reorder Point", f"{rop:,}")
    # display warning if rop is higher than eoq
    if rop > eoq:
        result_container.info("Since EOQ is less than ROP due to low handling cost, demand or holding cost, we will order in multiple of EOQ until it exceed ROP. In actual situation, combine them with other skus to yield much better overall costs")

    # calculate inventory level over 365 days
    data = calc_365_inventory(safety_stock, eoq, rop, demand_mean, demand_sd, leadtime_mean, leadtime_sd, random_demand_leadtime_boolean)

    # display matplotlib chart based on data    
    fig = px.line(data, x="day", y="inventory", title='Inventory levels over a year', labels={"day":"Number of days in a year", "inventory": "Inventory Level"})
    fig.add_hline(y=rop, line_dash="dash", line_color="orange", annotation_text="reorder point")
    fig.add_hline(y=safety_stock, line_dash="dash", line_color="green", annotation_text="safety stock")
    st.plotly_chart(fig, theme = 'streamlit')



# Preset Form
hub = preset_form.selectbox('Hub', sorted(df_combined['hub'].unique()), key='hub')
sku = preset_form.selectbox('SKU', sorted(df_combined['sku'].unique()), key='sku')
mode = preset_form.selectbox('Transport Mode', sorted(df_combined['mode'].unique()), key='mode')
preset_submit = preset_form.form_submit_button(label='Get Preset', on_click=preset, args = (hub, sku, mode))


# Data Form
service_level = data_form.slider('Desired service level for SKU (%)', 1, 100, 90, help="Higher service level will result in higher safety stock", key='service_level')
demand_mean = data_form_col1.number_input('Average monthly demand for SKU at hub', value = 1.0, min_value = 0.01, step = 1.0, format = "%f", help="Higher demand will result in higher safety stock, economic order quantity and reorder point", key='demand_mean')
demand_sd = data_form_col1.number_input('Standard deviation of monthly demand for SKU at hub', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher variability of demand month on month will result in higher safety stock", key='demand_sd')
leadtime_mean = data_form_col2.number_input('Average lead time from Marina Bay to hub (days)', value = 1.0, min_value = 0.01, step = 1.0, format = "%f", help="Longer lead time will result in higher safety stock and reorder point", key='leadtime_mean')
leadtime_sd = data_form_col2.number_input('Standard deviation of lead time from Marina Bay to hub (days)', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher variability of lead time will result in higher safety stock", key='leadtime_sd')
holding_cost_per_unit_per_month = data_form_col1.number_input('Holding cost per unit of SKU per month', value = 1.0, min_value = 0.01, step = 0.01, format = "%f", help="Higher holding cost will reduce the economic order quantity per order", key='holding_cost_per_unit_per_month')
handling_cost = data_form_col2.number_input('Handling cost per shipment order', value = 1.0, min_value = 0.01, step = 1.0, format = "%f", help="Higher handling cost per order will increase the economic order quantity per order", key='handling_cost')
random_demand_leadtime_boolean = data_form.checkbox("Simulate normalised random demand and leadtime", value=False, key='random_demand_leadtime', help="Enabling this will assuming randomised demand and leadtime normalised according to mean and standard deviation input")
data_submit1 = data_form.form_submit_button(label = "Submit", on_click = display_recommendations(service_level, demand_mean, demand_sd, leadtime_mean, leadtime_sd, holding_cost_per_unit_per_month, handling_cost, random_demand_leadtime_boolean))

import streamlit as st
import pandas as pd

#########################
## STREAMLIT STRUCTURE ##
#########################

st.set_page_config(layout="wide")

# Title of the page
st.title("Dashboard")
st.write("Summary of SKUs where stock days are limited and reorder date is near")



###############
## FUNCTIONS ##
###############
average_days_per_month = 30.437


# we need the following so that streamlit will only run the following once
# in this case, it will cache our df and not rerun it everytime we change something on the app
# https://discuss.streamlit.io/t/not-to-run-entire-script-when-a-widget-value-is-changed/502/5
@st.cache_data
def read_df_combined():
    df_combined = pd.read_csv('https://kyunomi-demo-s3.s3.ap-southeast-1.amazonaws.com/df_combined_sanitised.csv')
    # df_combined = pd.read_csv("df_combined.csv")
    df_combined["stock_month_2dp"] = df_combined["stock_month"].round(2)
    df_combined["stock_days_2dp"] = (df_combined["stock_month"]*average_days_per_month).round(2)
    df_combined["current_stock_formatted"] = df_combined["current_stock"].apply(lambda d: f"{int(d):,}")
    df_combined["avg_shipped_qty_2dp"] = df_combined["avg_shipped_qty"].round(2)
    st.session_state.df = df_combined
    return df_combined



if "df" not in st.session_state:
    st.session_state.df = read_df_combined()
read_df_combined()


def display_stock_warn_reorder(hub):
    stock_days_keys = "stock_days"+hub
    reorder_days_keys = "reorder_days"+hub

    # Stock Warning
    st.subheader(f"Stock Warning for {hub}")
    st.caption("Display stocks where remaining stock days is less than specified")
    st.slider("Stock Warning", 1, 90, 30, label_visibility = "collapsed", help = "Specify the stock days to filter", key = stock_days_keys)
    df_stock_warning = st.session_state.df[["sku","current_stock_formatted","avg_shipped_qty_2dp", "stock_days_2dp"]][(st.session_state.df["hub"]==hub) & (st.session_state.df["stock_days_2dp"] <= st.session_state[stock_days_keys])].groupby("sku").min().reset_index()
    df_stock_warning.columns = ["SKU","Stocks on hand", "Average monthly demand", "Stock days"]
    st.dataframe(df_stock_warning, use_container_width = True)

    # Reorder stocks. For CONSOLE hub only, remove the column "console_support"
    if hub == "CONSOLE":
        st.subheader(f"Upcoming Reorder for {hub}")
        st.caption("Display stocks where the reorder date is within the specified time period")
        st.caption("Recommended transport mode would always be based on the lowest estimated handling cost. If we have reorder date is marked as 0 (meaning we have already pass the optimum reorder date), recommended transport mode would be based on the shortest lead time")
        st.slider("Stock Warning", 1, 90, 30, label_visibility = "collapsed", help = "Specify the time period to filter upcoming reorder point", key = reorder_days_keys)
        df_reorder = st.session_state.df[["sku","current_stock_formatted", "avg_shipped_qty_2dp", "stock_days_2dp", "rop_date", "recommended_mode"]][(st.session_state.df["hub"]==hub) & (st.session_state.df["days_to_rop"] <= st.session_state[reorder_days_keys])].groupby("sku").min().reset_index()
        df_reorder.columns = ["SKU","Stocks on hand", "Average monthly demand", "Stock days", "Reorder Date", "Recommended Transport Mode"]
        st.dataframe(df_reorder, use_container_width = True)
    else:
        st.subheader(f"Upcoming Reorder for {hub}")
        st.caption("Display stocks where the reorder date is within the specified time period")
        st.caption("Recommended transport mode would always be based on the lowest estimated handling cost. If we have reorder date is marked as 0 (meaning we have already pass the optimum reorder date), recommended transport mode would be based on the shortest lead time")
        st.slider("Stock Warning", 1, 90, 30, label_visibility = "collapsed", help = "Specify the time period to filter upcoming reorder point", key = reorder_days_keys)
        df_reorder = st.session_state.df[["sku","current_stock_formatted", "avg_shipped_qty_2dp", "stock_days_2dp", "rop_date", "recommended_mode", "console_support"]][(st.session_state.df["hub"]==hub) & (st.session_state.df["days_to_rop"] <= st.session_state[reorder_days_keys])].groupby("sku").min().reset_index()
        df_reorder.columns = ["SKU","Stocks on hand", "Average monthly demand", "Stock days", "Reorder Date", "Recommended Transport Mode", "Support from Console Hub"]
        st.dataframe(df_reorder, use_container_width = True)        


###############
## STREAMLIT ##
###############
console_tab, CHANGI_tab, DHOBY_tab, SERANGOON_tab, SHENTON_tab = st.tabs(["CONSOLE", "CHANGI", "DHOBY", "SERANGOON", "SHENTON"])

with console_tab:
    display_stock_warn_reorder("CONSOLE")

with CHANGI_tab:
    display_stock_warn_reorder("CHANGI")

with DHOBY_tab:
    display_stock_warn_reorder("DHOBY")

with SERANGOON_tab:
    display_stock_warn_reorder("SERANGOON")
    
with SHENTON_tab:
    display_stock_warn_reorder("SHENTON")

import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from util import convert_date, revert_indian_number_format, format_numbers_to_indian_system
from data import Data
from update import UpdateCalls,historicData
import os
import logging
'''
main.py file with the functions to be used with different paths and triggers in app.py

load_data: a function to be used ideally before the site loads, to load the CSVs, make the "blacklist" i.e. the list with companies whose tickers arent available. Also makes the Date column to DateTime objects, returns list and company and calls df

process_data: process the data completely, and gives the required df as return

sort_data_frame: sorts the present dataframe with the passed value, returns the sorted df
'''

# data = Data()
# ohlcv = data.ohlcv
# brokerage_calls = data.brokerage_calls
# company_profile = data.company_profile



#load data to df from csv and load portfolio and other paths as well
def load_data(user):
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     parent_dir = os.path.dirname(current_dir)
#     #Path to the "ToBeIgnored" CSV file
#     #fpath = r'E:\python\ToBeIgnored.csv'
#     fpath = os.path.join(parent_dir,'csv_data','ToBeIgnored.csv')
#     #Path to list of unique analysts
#     #fpathanalysts=r'E:\python\UniqueAnalysts1.csv'
#     fpathanalysts=os.path.join(parent_dir,'csv_data','UniqueAnalysts1.csv')
#     #path to the Calls data CSV
#     # old file calls_data_file_path = r'E:\python\UpdatedCallsWithRecoPriceAndTickers.csv' 
#     #calls_data_file_path = r'E:\python\CallsWithUpdatedUpside.csv'
#     calls_data_file_path=os.path.join(parent_dir,'csv_data','CallsWithUpdatedUpside.csv')
#     #Historic stocks data CSV file path
#     # old file historic_company_data_file_path = r'E:\python\HistoricDataWithCompanyAgain.csv'
#    # historic_company_data_file_path = r'E:\python\HistoricDataFrom2018.csv'
#     historic_company_data_file_path=os.path.join(parent_dir,'csv_data','HistoricDataFrom2018.csv')
#     #portfolio_path=r'E:\python\StocksPortfolio.csv'
#     portfolio_path=os.path.join(parent_dir,'csv_data',f'User{user}csv_data','StocksPortfolio.csv')
#     try:
#         df_for_analysts=pd.read_csv(fpathanalysts)
#         df = pd.read_csv(fpath)
#         calls_df = pd.read_csv(calls_data_file_path)
#         history_df = pd.read_csv(historic_company_data_file_path)
#         #history_orders_path=r'E:\python\HistoryOrders.csv'
#         history_orders_path=os.path.join(parent_dir,'csv_data',f'User{user}csv_data','HistoryOrders.csv')
#         #stocks_track_path=r'E:\python\TrackingStocks.csv'
#         stocks_track_path = os.path.join(parent_dir,'csv_data',f'User{user}csv_data','TrackingStocks.csv')

        

#         list_of_unique_analysts=df_for_analysts['0']
#         #List containing companies whose data/ticker symbol is not correct
#         l1 = df['0'].tolist() 
#         company_list_temp=calls_df['Company'].unique().tolist()
#         company_list=[]
#         for i in company_list_temp:
#             if i not in l1:
#                 company_list.append(i)
#         # Converting the Date columns to DateTime objects
#         print(1)
#         calls_df['Date'] = calls_df['Date'].apply(convert_date)
#         print(2)
#         history_df['Date'] = history_df['Date'].apply(convert_date)
#         print(3)
#         calls_df['Reco']=calls_df['Reco'].round(2)
#         calls_df['Upside']=calls_df['Upside'].round(2)
#         unique_analysts = calls_df['Analyst'].unique()
#         # Create a dictionary to store DataFrames for each analyst
#         calls_df = calls_df.drop_duplicates(keep=False).reset_index(drop=True)
#         analyst_dfs = {analyst: df.reset_index(drop=True) for analyst,df in calls_df.groupby('Analyst')}

#         # Create a dictionary to store DataFrames for each company
#         company_data = {company: df.reset_index(drop=True).sort_values(by="Date",ascending=True) for company, df in history_df.groupby('Company')}
#         calls_by_company= {company: df.reset_index(drop=True).sort_values(by="Date",ascending=False) for company, df in calls_df.groupby('Company')}

#         for analyst in analyst_dfs:
#             analyst_dfs[analyst]=analyst_dfs[analyst].sort_values(by="Date",ascending=False)
#     except Exception as e:
#         raise RuntimeError(f"Error loading CSV files: {e}")

#     return stocks_track_path,history_orders_path,portfolio_path,company_list,l1, analyst_dfs, company_data,list_of_unique_analysts, calls_by_company, calls_df, history_df
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Define file paths
    fpath = os.path.join(parent_dir, 'csv_data', 'ToBeIgnored.csv')
    fpathanalysts = os.path.join(parent_dir, 'csv_data', 'UniqueAnalysts1.csv')
    calls_data_file_path = os.path.join(parent_dir, 'csv_data', 'CallsWithUpdatedUpside.csv')
    historic_company_data_file_path = os.path.join(parent_dir, 'csv_data', 'HistoricDataFrom2018.csv')
    portfolio_path = os.path.join(parent_dir, 'csv_data', f'User{user}csv_data', 'StocksPortfolio.csv')

    # Initialize return values
    stocks_track_path = os.path.join(parent_dir, 'csv_data', f'User{user}csv_data', 'TrackingStocks.csv')
    history_orders_path = os.path.join(parent_dir, 'csv_data', f'User{user}csv_data', 'HistoryOrders.csv')
    company_list = []
    l1 = []
    analyst_dfs = {}
    company_data = {}
    list_of_unique_analysts = []
    calls_by_company = {}
    calls_df = pd.DataFrame()
    history_df = pd.DataFrame()

    try:
        df_for_analysts = pd.read_csv(fpathanalysts)
        list_of_unique_analysts = df_for_analysts['0'].tolist()
    except Exception as e:
        logging.error(f"Error loading analysts file: {e}")

    try:
        df = pd.read_csv(fpath)
        calls_df = pd.read_csv(calls_data_file_path)
        history_df = pd.read_csv(historic_company_data_file_path)

        company_list_temp = calls_df['Company'].unique().tolist()
        company_list = [i for i in company_list_temp if i not in df['0'].tolist()]

        # Process DataFrames
        calls_df['Date'] = calls_df['Date'].apply(convert_date)
        history_df['Date'] = history_df['Date'].apply(convert_date)
        calls_df['Reco'] = calls_df['Reco'].round(2)
        calls_df['Upside'] = calls_df['Upside'].round(2)

        analyst_dfs = {analyst: df.reset_index(drop=True) for analyst, df in calls_df.groupby('Analyst')}
        company_data = {company: df.reset_index(drop=True).sort_values(by="Date", ascending=True) for company, df in history_df.groupby('Company')}
        calls_by_company = {company: df.reset_index(drop=True).sort_values(by="Date", ascending=False) for company, df in calls_df.groupby('Company')}
        
        for analyst in analyst_dfs:
            analyst_dfs[analyst] = analyst_dfs[analyst].sort_values(by="Date", ascending=False)
    
    except Exception as e:
        logging.error(f"Error loading or processing data: {e}")

    return stocks_track_path, history_orders_path, portfolio_path, company_list, l1, analyst_dfs, company_data, list_of_unique_analysts, calls_by_company, calls_df, history_df





def process_data(start_date, end_date, dur, analyst_to_be_displayed, l1, analyst_dfs, company_data):

    # Use dur to set corresponding 'x' i.e. periods to focus on for success by using timedelta
    if dur == "1Y":
        x = datetime.timedelta(days=365)
    elif dur == "6M":
        x = datetime.timedelta(days=182)
    elif dur == "3M":
        x = datetime.timedelta(days=91)

    # List of the analysts who have to be processed
    to_be_processed = []

    #Dictionary for the calls for each analyst to be processed in the form dict[Analyst]= Dataframe segment to be processed
    calls_to_be_processed = {}
    calls_after=datetime.date(2018,1,1)

    if analyst_to_be_displayed == 'All':
        to_be_processed = list(analyst_dfs.keys())
    else:
        to_be_processed = [analyst_to_be_displayed]
   # print(to_be_processed)
    #dictionary to be converted to df finally
    final_dict = {}
    unique_company={}
    # Traverses all analysts available
    for broker in analyst_dfs:
     #   print(broker)
        #All analysts in the list
        if broker in to_be_processed:
            
            # if the start date is less than the first call made by the broker and end date is greater than that
            # Need to put a warning message that pops up to warn the user but not hinder the process
            if start_date < analyst_dfs[broker]['Date'].iloc[-1]:
                if end_date >= analyst_dfs[broker]['Date'].iloc[-1]:

                    # filtered_df consisting of all the calls made between the dates and with the company not in l1
                    filtered_df = analyst_dfs[broker][
                        (analyst_dfs[broker]['Date'] >= start_date) & (analyst_dfs[broker]['Date'] <= end_date) & (
                            ~analyst_dfs[broker]['Company'].isin(l1)) & (analyst_dfs[broker]['Date'] >= calls_after)&(analyst_dfs[broker]['To Be Taken']==1)]
                    #print(filtered_df)
                    calls_to_be_processed[broker] = filtered_df.reset_index(drop=True)
                #if end date is also less than the first call
                else:
                    continue
            else:

                # filtered_df consisting of all the calls made between the dates and with the company not in l1
                filtered_df = analyst_dfs[broker][
                    (analyst_dfs[broker]['Date'] >= start_date) & (analyst_dfs[broker]['Date'] <= end_date) & (
                        ~analyst_dfs[broker]['Company'].isin(l1)) & (analyst_dfs[broker]['Date'] >= calls_after) &(analyst_dfs[broker]['To Be Taken']==1)]
                #print(filtered_df)
                calls_to_be_processed[broker] = filtered_df
    # the calls_to_be_processed dictionary to later be used to showcase on the frontend all the calls considered while doing the analysis of a given broker 

   # print(calls_to_be_processed)
    for broker in calls_to_be_processed:
        bdf = calls_to_be_processed[broker]
        sum_for_average=0
        sum_for_avg_return=0
        sum_for_avg_per_day=0
        avg_return_count=0
        calls = 0
        successes = 0
        percentage=0 
        broker_company={}
        # histogram=[]
        for tar, adv, dat, com, reco in zip(bdf['Target'], bdf['Advice'], bdf['Date'], bdf['Company'],bdf["Reco"]):
            tar = float(tar)
            reco = float(reco)
            call_date = dat
            till_date = call_date + x #x created from dur at the beginning
            cdf=company_data[com]
            reach =0
            #if latest data is older than the till date, continue
            if cdf['Date'].iloc[-1] < till_date:
                continue
            calls += 1
            if com not in broker_company:
                broker_company[com]=1
            else:
                broker_company[com]+=1

            # need to do this using reco price asap
            # if all these them reach using high else using low
            if reco !=None:
                if reco<tar:
                    reach = cdf['High'][
                    (cdf['Date'] >= call_date) & (cdf['Date'] <= till_date)].max()
                else:
                    reach = cdf['Low'][
                    (cdf['Date'] >= call_date) & (cdf['Date'] <= till_date)].min()
            else:
                if adv in ['Buy', 'Neutral', 'Hold', 'Accumulate']:
                    #defining reach as the highest point the company reached in the given period to be compared with the target to deem success
                    reach = cdf['High'][
                        (cdf['Date'] >= call_date) & (cdf['Date'] <= till_date)].max()
                else:

                    #defining reach as the lowest point the company reached in the given period to be compared with the target to deem success
                    reach = cdf['Low'][
                        (cdf['Date'] >= call_date) & (cdf['Date'] <= till_date)].min()

            # isna checks if the value is NaN
            if reach is not None and not pd.isna(reach) and not pd.isna(tar):
                if reco is not None:
                    if (reco < tar and reach >= tar) or (reco > tar and reach <= tar):
                        successes += 1

                else:
                    if (adv in ['Buy', 'Neutral', 'Hold', 'Accumulate'] and reach >= tar) or (adv not in ['Buy', 'Neutral', 'Hold', 'Accumulate'] and reach <= tar):
                        successes += 1
                
                if reco is not None:

                    if (reco < tar and reach >= tar):  
                        cdf_dates = cdf["Date"].to_numpy()
                        # Find the index where the call_date would fit in the sorted array
                        start_index = np.searchsorted(cdf_dates, call_date)

                        # Make sure that start_index is within the bounds of the dataframe
                        start_index = min(start_index, len(cdf) - 1)
                        for d,h in zip(cdf["Date"].iloc[start_index:], cdf["High"].iloc[start_index:]):
                            if h>=tar:
                                avg_return_count+=1
                                avg_return=(tar-reco)/reco
                                sum_for_avg_return+=avg_return
                                sum_for_avg_per_day+=avg_return/int((d-call_date).days) if int((d-call_date).days)!=0 else 0
                                sum_for_average+=(d-call_date).days
                                # histogram.append((d-call_date).days)
                                break
                    elif (reco > tar and reach <= tar):
                        cdf_dates = cdf["Date"].to_numpy()

                        # Find the index where the call_date would fit in the sorted array
                        start_index = np.searchsorted(cdf_dates, call_date)

                        # Make sure that start_index is within the bounds of the dataframe
                        start_index = min(start_index, len(cdf) - 1)
                        for d,l in zip(cdf["Date"].iloc[start_index:], cdf["Low"].iloc[start_index:]):
                            if l<=tar:
                                #sum_for_average+=(d-call_date).days
                                #histogram.append((d-call_date).days)

                                break
                else:
                    if (adv in ['Buy', 'Neutral', 'Hold', 'Accumulate'] and reach >= tar):  
                        cdf_dates = cdf["Date"].to_numpy()

                        # Find the index where the call_date would fit in the sorted array
                        start_index = np.searchsorted(cdf_dates, call_date)

                        # Make sure that start_index is within the bounds of the dataframe
                        start_index = min(start_index, len(cdf) - 1)
                        for d,h in zip(cdf["Date"].iloc[start_index:], cdf["High"].iloc[start_index:]):
                            if h>=tar:
                                
                                #sum_for_average+=(d-call_date).days
                               #histogram.append((d-call_date).days)
                                break
                    elif (adv not in ['Buy', 'Neutral', 'Hold', 'Accumulate'] and reach <= tar):
                        cdf_dates = cdf["Date"].to_numpy()
                        # Find the index where the call_date would fit in the sorted array
                        start_index = np.searchsorted(cdf_dates, call_date)

                        # Make sure that start_index is within the bounds of the dataframe
                        start_index = min(start_index, len(cdf) - 1)
                        
                        for d,l in zip(cdf["Date"].iloc[start_index:], cdf["Low"].iloc[start_index:]):
                            if l<=tar:
                                #sum_for_average+=(d-call_date).days
                                #histogram.append((d-call_date).days)
                                break
        average_return=round((sum_for_avg_return/avg_return_count)*100,2) if avg_return_count!=0 else 0
        average_return_per_day=round((sum_for_avg_per_day/avg_return_count)*100,2) if avg_return_count!=0 else 0
        average_upside_reco=bdf['Upside'].mean()
        median_upside_reco=bdf['Upside'].median()
        unique_stocks=len(broker_company)
        percentage = (successes / calls) * 100 if calls != 0 else 0
        percentage = round(percentage, 1)
        avg_time = int((sum_for_average /successes)) if successes!=0 else 0
        final_dict[broker] = {"Total Calls in Period: ": calls,
                              "Total Successes in the period: ": successes,
                              "Success %": percentage,
                              "Average days taken by successful calls" : avg_time,
                              "No. of Unique Stocks":unique_stocks,
                              "Average Return For Applicable Calls":average_return,
                              "Average Return Per Day":average_return_per_day,
                              "Number of calls considered for average return":avg_return_count,
                              "Average Upside Reco":round(average_upside_reco,2),
                              "Median Upside Reco": round(median_upside_reco,2)}
        unique_company[broker]=pd.DataFrame([broker_company], index=[broker]).transpose().sort_values(by=broker,ascending=False)
    # histogram_df=pd.DataFrame(histogram)
    # histogram_df.to_csv(r'E:\python\AvgTimeCheckHistogramBuySuccess.csv',index=False)
    # final_df that is used to render the df
    final_df = pd.DataFrame.from_dict(final_dict, orient='index')
    if len(final_df) >= 1:
        #final_df = final_df.sort_values(by='Success %', ascending=False)
        final_df['Weighted Total Number of Calls']=(np.tanh(final_df['Total Calls in Period: ']*0.0025))
        final_df['Weighted Success %']=(final_df['Weighted Total Number of Calls']*final_df['Success %'])
        final_df=sort_data_frame(final_df, "Weighted Success %")
        #df_rank_process['Weighted Total Number of Calls']=round(df_rank_process['Weighted Total Number of Calls'],2)
        final_df['Weighted Success %']=round(final_df['Weighted Success %'],2)

    if final_df is not None:
        format_numbers_to_indian_system(final_df, ["Total Calls in Period: ", "Total Successes in the period: "])
    return final_df,calls_to_be_processed, unique_company

#sort analyst view df (final_df)
def sort_data_frame(final_df, sort_by):
    final_df = revert_indian_number_format(final_df, ["Total Calls in Period: ", "Total Successes in the period: "])
    final_df = final_df.sort_values(by=sort_by, ascending=False)
    final_df = format_numbers_to_indian_system(final_df, ["Total Calls in Period: ", "Total Successes in the period: "])
    return final_df

#stocks_df processing
def hot_stocks_backend(start_date,end_date,calls_by_company, l1):
    companies = []
    number_of_calls = []
    calls_by_company_stocks={}
    for company in calls_by_company:
        if company not in l1:
            calls_by_company_stocks[company]=calls_by_company[company][(calls_by_company[company]['Date']>=start_date)&(calls_by_company[company]['Date']<=end_date)]
    for company in calls_by_company_stocks:
        if company not in l1:
            companies.append(company)
            number_of_calls.append(len(calls_by_company_stocks[company]))
    
    # Create a DataFrame from dictionaries or tuples where each tuple is a separate row
    data = {'Company': companies, 'Number of calls made': number_of_calls}
    stocks_details_df = pd.DataFrame(data)
    
    # Sort DataFrame by 'Number of calls made' in descending order
    stocks_details_df = stocks_details_df.sort_values(by="Number of calls made", ascending=False)
    
    return stocks_details_df,calls_by_company_stocks

def recommended_stocks(mcap,upside_filter,upside_factor_weight,start_date, end_date, dur, analyst_dfs, company_data,rank_consider,sort_by,priority,period,num,calls_df,l1,analyst_rank):
    #dfm=pd.read_csv(r'E:\python\WithMarketCap.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    path_needed=os.path.join(parent_dir,'csv_data','WithMarketCap.csv')
    dfm=pd.read_csv(path_needed)
    dfm.set_index('Company', inplace=True)
    dfm=dfm.transpose()
    dict1=dfm.to_dict()
    dict_for_weight={
        '100%':1.0,
        '90%':0.9,
        '80%':0.8,
        '70%':0.7,
        '60%':0.6,
        '50%':0.5,
        '40%':0.4,
        '30%':0.3,
        '20%':0.2,
        '10%':0.1,
        '0%':0.0,
    }
    dict_for_upside_filte={
        '10%':10.0,
        '15%':15.0,
        '20%':20.0,
        '0%':0.0
    }
    dict_for_mkt_cap_filter={
        '0-500':0.0,
        '500-2k':500.0,
        '2k-5k':2000.0,
        '5k-20k':5000.0,
        '20k+':20000.0,
        'All':0.0
    }
    min_mcap=dict_for_mkt_cap_filter[mcap]
    if mcap=='0-500':
        max_mcap=500.0
    elif mcap=='500-2k':
        max_mcap=2000.0
    elif mcap=='2k-5k':
        max_mcap=5000.0
    elif mcap=='5k-20k':
        max_mcap=20000.0
    elif mcap=='20k+':
        max_mcap=100000000000000000000.0
    if num!='All':
        top_=int(num)
    else:
        top_=None
    priority=priority
    sort_by=sort_by
    
    if period=='1D':
        x=1
    elif period=='5D':
        x=5
    elif period=='7D':
        x=7
    elif period=='15D':
        x=12
    elif period=='30D':
        x=30
    elif period=='120D':
        x=120
    back=datetime.timedelta(days=x)
    #today=datetime.date(2024,6,18)
    today=datetime.date.today()
    till = today -back
    calls_for_rec=calls_df[(calls_df['Date']>=till)&(calls_df['To Be Taken']==1)&(calls_df['Date']<=today)&(~calls_df['Company'].isin(l1))]
    unique_tickers = [ticker.strip() for ticker in calls_for_rec['Ticker'].unique().tolist()]
    today_str=str(datetime.date.today())
    data_ltp = yf.download(unique_tickers, start=today_str)['Close']
    xtoday=datetime.date.today()
    while data_ltp.empty:
        xtoday= xtoday-datetime.timedelta(days=1)
        today_str1=str(xtoday)
        data_ltp = yf.download(unique_tickers, start=today_str1)['Close']
    
    data_ltp=data_ltp.transpose()
    # dict1={tick:df['Close'] for tick, df in data.groupby('Ticker') }
    # print(dict1)
    if not data_ltp.empty:
        dict_ltp = data_ltp.iloc[:, 0].to_dict()
    rec_all_calls= {company: df.sort_values(by="Date",ascending=False).reset_index(drop=True) for company, df in calls_for_rec.groupby('Company')}
    recommendations={}
    if rank_consider=='no':
        for company, tempdf in rec_all_calls.items():
            num_analyst = int(len(tempdf))
            max_target = round(tempdf["Target"].max(),2) if not tempdf.empty else None
            min_target = round(tempdf["Target"].min(),2) if not tempdf.empty else None
            mean_target = round(tempdf["Target"].mean(),2) if not tempdf.empty else None
            max_upside =round(tempdf["Upside"].max(),2) if not tempdf.empty else None
            min_upside = round(tempdf["Upside"].min(),2) if not tempdf.empty else None
            mean_upside = round(tempdf["Upside"].mean(),2) if not tempdf.empty else None
            if company in dict1:
                if 'Market Cap' in dict1[company]:
                    market_cap=round(((dict1[company]['Market Cap'])/10000000),2)
                else:
                    market_cap=None
            else:
                market_cap=None            
            
            
            ltp = 0
            tick = tempdf.iloc[0]['Ticker'] if not tempdf.empty else None
            if tick:
                try:
                    ticker_info = yf.Ticker(tick)
                    data = ticker_info.history(period='1d')

                    if not data.empty:
                        ltp = round(data['Close'].iloc[-1],2)
                    else:
                        print(f"No data available for {tick}")
                        continue  # Skip this iteration if no data is available

                except Exception as e:
                    print(f"Error occurred for {tick}: {e}")
                    continue  # Skip this iteration or handle the error
            if mean_upside>=10:
                recommendations[company] = {
                    'Average Upside': mean_upside,
                    'Average Target': mean_target,
                    'Number of Recommendations': num_analyst,
                    'LTP': ltp,
                    'Max Target': max_target,
                    'Minimum Target': min_target,
                    'Max Upside': max_upside,
                    'Minimum Upside': min_upside,
                    'Market Cap':market_cap
                }
    elif rank_consider=='yes':
        up_filter=dict_for_upside_filte[upside_filter]
        analyst_rank,df_full,dict_full =rankgen(start_date, end_date, dur, analyst_dfs, company_data, l1,analyst_rank)
        for i in rec_all_calls:
            successper=[]
            for index,row in rec_all_calls[i].iterrows():
                if row['Analyst'] in dict_full:
                    successper.append(dict_full[row['Analyst']]['Success %'])
                else:
                    successper.append(None)
            rec_all_calls[i]['Success %']=successper
        for company, tempdf in rec_all_calls.items():
            #and company!='Amara Raja Energy & ..'
            if company not in l1 :
                num_analyst = int(len(tempdf))
                traded_value=0
                recom_tradeable_value=0
                max_target = round(tempdf["Target"].max(),2) if not tempdf.empty else None
                min_target = round(tempdf["Target"].min(),2) if not tempdf.empty else None
                mean_target = round(tempdf["Target"].mean(),2) if not tempdf.empty else None
                max_upside =round(tempdf["Upside"].max(),2) if not tempdf.empty else None
                min_upside = round(tempdf["Upside"].min(),2) if not tempdf.empty else None
                mean_upside = round(tempdf["Upside"].mean(),2) if not tempdf.empty else None
                if company in dict1:
                    if 'Market Cap' in dict1[company]:
                        if not pd.isna(dict1[company]['Market Cap']):
                          market_cap=int(round((float(dict1[company]['Market Cap'])/10000000),0))
                        else:
                            market_cap=None
                    else:
                        market_cap=None
                else:
                    market_cap=None
                ltp = 0
                tick = tempdf.iloc[0]['Ticker'] if not tempdf.empty else None
                if tick and tick in dict_ltp and not pd.isna(dict_ltp[tick]):
                    ltp=dict_ltp[tick]
                else:
                    if tick:
                        try:
                            ticker_info = yf.Ticker(tick)
                            data = ticker_info.history(period='1d')

                            if not data.empty:
                                ltp = round(data['Close'].iloc[-1],2)
                            else:
                                print(f"No data available for {tick}")
                                continue  # Skip this iteration if no data is available

                        except Exception as e:
                            print(f"Error occurred for {tick}: {e}")
                            continue  # Skip this iteration or handle the error
                weighted_upside_sum=0
                weighted_target_sum=0
                cumulative_wt=0
                wt_calls=0
                for index, row in tempdf.iterrows():
                    analyst=row['Analyst'] 
                    if analyst in analyst_rank:
                        w=analyst_rank[analyst]
                    else:
                        w=0

                    cumulative_wt+=w
                    wt_calls=round(cumulative_wt,2)
                    weighted_target_sum+=(w)*(float(row["Target"]))
                    weighted_upside_sum+=(w)*(float(row["Upside"]))
                avg_traded_volume=(company_data[company]['Volume'].tail(20).sum())/20
                recom_tradeable_value=round(((avg_traded_volume*ltp)*0.05)/(10**7),2)
                traded_value=round((avg_traded_volume*ltp)/(10**7),2)
                

                weighted_upside =round(weighted_upside_sum/cumulative_wt,2)if cumulative_wt!=0 else 0
                weighted_target=round(weighted_target_sum/cumulative_wt,2) if cumulative_wt!=0 else 0
                min_upside_ltp=round(((min_target-ltp)/ltp)*100,2) if ltp != 0 else None
                max_upside_ltp=round(((max_target-ltp)/ltp)*100,2) if ltp != 0 else None
                mean_upside_ltp=round(((mean_target-ltp)/ltp)*100,2) if ltp != 0 else None
                weighted_upside_ltp=round(((weighted_target-ltp)/ltp)*100,2) if ltp != 0 else None
                if mcap=='All':
                    
                    if mean_upside>=0 and weighted_upside_ltp>up_filter:
                        recommendations[company] = {
                        'Average Upside': mean_upside,
                        'Average Target': mean_target,
                        'Number of Recommendations': num_analyst,
                        'LTP': ltp,
                        'Max Target': max_target,
                        'Minimum Target': min_target,
                        'Max Upside': max_upside,
                        'Minimum Upside': min_upside,
                        'Weighted Upside':weighted_upside,
                        'Weighted Target':weighted_target,
                        'Market Cap':market_cap,
                        'Max Upside Current': max_upside_ltp,
                        'Minimum Upside Current': min_upside_ltp,
                        'Average Upside Current':mean_upside_ltp,
                        'Weighted Number of Calls':wt_calls,
                        'Weighted Upside Current':weighted_upside_ltp,
                        'Recommended Trade Value':recom_tradeable_value,
                        'Average Traded Value':traded_value
                    }
                else:
                    if mean_upside>=0 and weighted_upside_ltp>up_filter and market_cap>min_mcap and market_cap<max_mcap:
                        recommendations[company] = {
                        'Average Upside': mean_upside,
                        'Average Target': mean_target,
                        'Number of Recommendations': num_analyst,
                        'LTP': ltp,
                        'Max Target': max_target,
                        'Minimum Target': min_target,
                        'Max Upside': max_upside,
                        'Minimum Upside': min_upside,
                        'Weighted Upside':weighted_upside,
                        'Weighted Target':weighted_target,
                        'Market Cap':market_cap,
                        'Max Upside Current': max_upside_ltp,
                        'Minimum Upside Current': min_upside_ltp,
                        'Average Upside Current':mean_upside_ltp,
                        'Weighted Number of Calls':wt_calls,
                        'Weighted Upside Current':weighted_upside_ltp,
                        'Recommended Trade Value':recom_tradeable_value,
                        'Average Traded Value':traded_value
                    }

    recommendation_df=pd.DataFrame(recommendations).transpose()
    if len(recommendation_df)>1:
        recommendation_df=recommendation_df.sort_values(by=priority, ascending=False)
        #recommendation_df=recommendation_df.head(top_)
        k=1.4
        wup=dict_for_weight[upside_factor_weight]
        wnum =1-wup
        call_mid=(recommendation_df['Weighted Number of Calls'].max()+1)/2
        #recommendation_df['Norm Wt Num Calls']= ((recommendation_df['Weighted Number of Calls']-recommendation_df['Weighted Number of Calls'].min())/(recommendation_df['Weighted Number of Calls'].max()-recommendation_df['Weighted Number of Calls'].min()))
        #recommendation_df['Norm Wt Num Calls']= (1/(1+(np.exp(-k*(recommendation_df['Weighted Number of Calls']-call_mid)))))
        #recommendation_df['Norm Wt Avg Upside Curr']= (recommendation_df['Weighted Upside Current']-(recommendation_df['Weighted Upside Current']).min())/((recommendation_df['Weighted Upside Current']).max()-(recommendation_df['Weighted Upside Current']).min())
        #recommendation_df['Norm Wt Avg Upside Curr']=np.log(recommendation_df['Weighted Upside Current']+1.0)
        #recommendation_df['Norm Wt Avg Upside Curr']=((recommendation_df['Norm Wt Avg Upside Curr']-recommendation_df['Norm Wt Avg Upside Curr'].min())/(recommendation_df['Norm Wt Avg Upside Curr'].max()-recommendation_df['Norm Wt Avg Upside Curr'].min()))
        recommendation_df['Norm Wt Avg Upside Curr']=(np.tanh(recommendation_df['Weighted Upside Current']*0.05))
        recommendation_df['Norm Wt Num Calls']=(np.tanh(recommendation_df['Weighted Number of Calls']*0.3))
        #recommendation_df['Norm Wt Num Calls']=np.log(recommendation_df['Weighted Number of Calls']+1.0)
        #recommendation_df['Norm Wt Num Calls']=((recommendation_df['Norm Wt Num Calls']-recommendation_df['Norm Wt Num Calls'].min())/(recommendation_df['Norm Wt Num Calls'].max()-recommendation_df['Norm Wt Num Calls'].min()))

        recommendation_df['Final Factor']=wnum*recommendation_df['Norm Wt Num Calls']+wup*recommendation_df['Norm Wt Avg Upside Curr']
        
        recommendation_df['Norm Wt Num Calls']=recommendation_df['Norm Wt Num Calls'].round(2)
        recommendation_df['Norm Wt Avg Upside Curr']=recommendation_df['Norm Wt Avg Upside Curr'].round(2)
        recommendation_df['Final Factor']=recommendation_df['Final Factor'].round(2)
    if len(recommendation_df)>1:
        recommendation_df=recommendation_df.sort_values(by=sort_by,ascending=False)
        recommendation_df=format_numbers_to_indian_system(recommendation_df,['Market Cap','LTP'])
    return recommendation_df,rec_all_calls
        
def rankgen(start_date, end_date, dur, analyst_dfs, company_data, l1,analyst_rank):
    def custom_curve_transform(x):
    # Exponential-like growth initially
        y = (np.exp(x / 7) - 1)**0.6
        
        # Curve down effect
        y = y * (1 - (x / 100)**2)
        
        # Normalize to range 0-1
        y_normalized = (y - np.min(y)) / (np.max(y) - np.min(y))
        
        return y_normalized
    df_rank_process,x,y=process_data(start_date, end_date, dur, 'All', l1, analyst_dfs, company_data)
    sort_data_frame(df_rank_process, "Success %")
    df_rank_process=revert_indian_number_format(df_rank_process, ["Total Calls in Period: ", "Total Successes in the period: "])
    call_mid=(df_rank_process['Total Calls in Period: '].max() +1)/2
    k=0.0012
    #df_rank_process['Weighted Total Number of Calls']= (1/(1+(np.exp(-k*(df_rank_process['Total Calls in Period: ']-call_mid)))))
    df_rank_process['Weighted Total Number of Calls']=(np.tanh(df_rank_process['Total Calls in Period: ']*0.0025))
    #df_rank_process['Normalised Success %']= custom_curve_transform(df_rank_process['Success %'])
    df_rank_process['Weighted Success %']=(df_rank_process['Weighted Total Number of Calls']*df_rank_process['Success %'])
    #df_rank_process['Weighted Success %']=(df_rank_process['Weighted Total Number of Calls']*df_rank_process['Normalised Success %'])
    df_rank_process=sort_data_frame(df_rank_process, "Weighted Success %")
    df_rank_process['Weighted Total Number of Calls']=round(df_rank_process['Weighted Total Number of Calls'],2)
    df_rank_process['Weighted Success %']=round(df_rank_process['Weighted Success %'],2)
    ########df_rank_process.to_csv(r'E:\python\ForHistogram.csv')
    df_rank_process2=df_rank_process.transpose()
    dict1=df_rank_process2.to_dict()
    # for i in dict1:
    #     temp_df1=dict1[i]
    #     temp_df2=analyst_dfs[i]
    #     if not temp_df1.empty and not temp_df2.empty:
    count =0
    score=[]
    n=len(dict1)
    for i in dict1:
        x= round((n-count)/n,4)
        count+=1
        analyst_rank[i]=x
        score.append(x)
    df_rank_process['Score']=score
    #print(analyst_rank)
    return analyst_rank, df_rank_process,dict1


def return_ltp(company):
    #df=pd.read_csv(r'E:\python\CompanyMasterUpdate.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    path_needed=os.path.join(parent_dir,'csv_data','CompanyMasterUpdate.csv')
    df=pd.read_csv(path_needed)
    ticker=df[df['Company']==company]['Ticker'].iloc[-1]
    ticker_info = yf.Ticker(ticker)
    data = ticker_info.history(period='1d')
    if not data.empty:
        ltp = round(data['Close'].iloc[-1],2)
    return ltp if ltp else None

def portfolio_updates(portfolio_path):
    update_df=pd.DataFrame(columns=['Remarks'])
    dfp=pd.read_csv(portfolio_path)
    #csv_file_path = r'E:\python\CallsWithUpdatedUpside.csv'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    try:
        path_needed=os.path.join(parent_dir,'csv_data','CallsWithUpdatedUpside.csv')
        df=pd.read_csv(path_needed)
        #df=pd.read_csv(csv_file_path)
        df['Date']=df['Date'].apply(convert_date)
        df=df[df['Date']>=(datetime.date.today()-datetime.timedelta(days=4))]
        comp=df['Company'].unique().tolist()
        checked=[]
        for index,row in dfp.iterrows():
            if row['Company'] not in checked:
                checked.append(row['Company'])
                ltp=return_ltp(row['Company'])
                if float(row['Price Bought At'])>float(ltp):
                    string1=f"Current price of {row['Company']} fell below bought price, Current price is INR {ltp}, loss of {round(((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100,2)}% "
                    update_df.loc[len(update_df)] = [string1]
                elif row['Target']<=ltp:
                    string1=f"Target achieved of {row['Company']}, current return {round(((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100,2)}%"
                    update_df.loc[len(update_df)] = [string1]
        
        checked=[]

        for index,row in dfp.iterrows():
            
            if row['Company'] in comp and row['Company'] not in checked:
                checked.append(row['Company'])
                for dindex,drow in df.iterrows():
                    if row['Company'] ==drow['Company']:
                        if float(drow['Upside']<0):
                            string1=f"Downside call on {row['Company']} by {drow['Analyst']} of {round(drow['Upside'],2)}%"
                            update_df.loc[len(update_df)] = [string1]
                        else:
                            string1=f"Upside call on {row['Company']} by {drow['Analyst']} of {round(drow['Upside'],2)}%"
                            update_df.loc[len(update_df)] = [string1]

    except Exception as e:
        logging.error(f"Error rendering portfolio updates probably because of calls df not loading: {e}")
        update_df.loc[len(update_df)] =['Error rendering update df']
    return update_df


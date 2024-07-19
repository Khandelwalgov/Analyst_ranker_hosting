import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import datetime
import yfinance as yf
import pandas as pd
from util import convert_date
import os
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
import tarfile
import zipfile
import platform
import requests
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


def UpdateCalls():
    url = 'https://trendlyne.com/research-reports/all/'

    # def download_geckodriver():
    #     system = platform.system().lower()
    #     machine = platform.machine().lower()

    #     if system == "windows":
    #         geckodriver_url = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-win64.zip"
    #         geckodriver_zip_path = "geckodriver.zip"
    #         extract_path = "geckodriver"
    #     elif system == "linux" and machine == "aarch64":
    #         geckodriver_url = "https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz"
    #         geckodriver_zip_path = "geckodriver.tar.gz"
    #         extract_path = "geckodriver"
    #     else:
    #         raise Exception(f"Unsupported platform: {system} {machine}")

    #     # Download Geckodriver
    #     response = requests.get(geckodriver_url)
    #     with open(geckodriver_zip_path, 'wb') as file:
    #         file.write(response.content)

    #     # Extract Geckodriver
    #     if system == "windows":
    #         with zipfile.ZipFile(geckodriver_zip_path, 'r') as zip_ref:
    #             zip_ref.extractall(extract_path)
    #         geckodriver_path = os.path.join(extract_path, "geckodriver.exe")
    #     else:
    #         with tarfile.open(geckodriver_zip_path) as tar_ref:
    #             tar_ref.extractall(extract_path)
    #         geckodriver_path = os.path.join(extract_path, "geckodriver")
    #         os.chmod(geckodriver_path, 0o755)

    #     return geckodriver_path


    def keep(till_company,till_analyst,csv_file_path, from_date, df, driver,dict1):  
        go_on = True
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('tbody', id='allreportsbody')
        data = []

        if table:
            rows = table.find_all('tr')
            for row in rows:
                date = ''
                company = ''
                analyst = ''
                target = ''
                advice = ''
                ticker = ''
                reco = ''

                advice_div_list = row.find_all('td', class_='invisible-details-control')
                if len(advice_div_list) > 1:
                    advice_span = advice_div_list[5].find('span', class_='fs085rem')
                    if advice_span and advice_span.text.strip() in ['Buy', 'Hold', 'Sell', 'Neutral', 'Accumulate']:
                        advice = advice_span.text.strip()
                    else:
                        continue
                
                date_td = row.find('td', class_='rightAlgn upcase invisible-details-control sorting_1')
                if date_td:
                    date = convert_date(date_td.text.strip())
                    
                
                company_td = row.find('td', class_='lAlign fw500')
                if company_td:
                    company = company_td.a.text.strip()
                
                analyst_td = row.find('td', class_='mW120 lAlign')
                if analyst_td:
                    analyst = analyst_td.a.text.strip()
                    label_element = analyst_td.find('label', {'class': 'label'})
                    if label_element:
                        data_original_title = label_element.get('title', '')
                        if 'for' in data_original_title:
                            ticker = data_original_title.split('for ')[-1]
                if date and company and analyst and date == from_date and analyst==till_analyst and company==till_company:
                        go_on = False
                        break
                td_element = row.find('td', class_='rightAlgn negative invisible-details-control')
                if td_element:
                    reco = td_element.contents[0].strip()
                else:
                    td_element = row.find('td', class_="rightAlgn positive invisible-details-control")
                    if td_element:
                        reco = td_element.contents[0].strip()

                target_td_list = row.find_all('td', class_='rightAlgn invisible-details-control')
                if len(target_td_list) > 1:
                    target = target_td_list[1].text.strip()
                if company in dict1:
                    ticker=dict1[company]['Ticker']
                    to_be_taken=1 if dict1[company]['to be taken']!= 0 else None
                    long_name=dict1[company]['Long Name']
                    target_clean = target.strip()  # Remove leading/trailing whitespace
                    reco_clean = reco.strip()  # Remove leading/trailing whitespace
                    if not target_clean or not reco_clean:
                        # Handle case where either target or reco is empty after stripping
                        upside=None
                    else:
                    # Convert to float after stripping whitespace
                        target_float = float(target_clean)
                        reco_float = float(reco_clean)
                        
                        if reco_float != 0:  # Ensure division by zero is avoided
                            upside =round(((target_float - reco_float) / reco_float)*100,2)
                        else:
                            upside = None  # or handle division by zero cas
                    market_cap=dict1[company]['Market Cap']
                    data.append([advice, company, target, analyst, date, ticker, reco,upside,long_name,market_cap,to_be_taken])
                    print([advice, company, target, analyst, date, ticker, reco,upside,long_name,market_cap,to_be_taken])

        if data:
            
            columns = ["Advice", "Company", "Target", "Analyst", "Date", "Ticker", "Reco","Upside","Long Name", "Market Cap","To Be Taken"]
            df = pd.DataFrame(data, columns=columns)
        return go_on, df

    def click_load_more(driver):
        try:
            load_more_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="endless_more btn btn-lg dblock"]')))
            if load_more_button:
                driver.execute_script("arguments[0].click();", load_more_button)
                return True
        except Exception as e:
            return False
        
    #csv_file_path = r'E:\python\CallsWithUpdatedUpside.csv'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    csv_file_path=os.path.join(parent_dir,'csv_data','CallsWithUpdatedUpside.csv')
    
    columns = ["Advice", "Company", "Target", "Analyst", "Date", "Ticker", "Reco"]
    df = pd.DataFrame(columns=columns)

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')  
        driver = webdriver.Chrome(options=chrome_options)
    elif system == "linux":
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')  
        service = Service(executable_path='/usr/bin/')
        driver = webdriver.Chrome(service=service,options=chrome_options)
    
    # firefox_options = Options()
    # firefox_options.add_argument('--headless')  # Run in headless mode
    # firefox_options.add_argument('--disable-gpu')  

    # # Initialize Firefox WebDriver
    # driver = webdriver.Firefox(executable_path=r"C:\Users\HP\geckodriver-v0.34.0-win32",options=firefox_options)
    # geckodriver_path = download_geckodriver()
    # firefox_options = webdriver.FirefoxOptions()
    # firefox_options.add_argument('--headless')  # Example option
    # service = Service(executable_path=GeckoDriverManager().install())
    # service = Service(executable_path=geckodriver_path)


    # Start Firefox WebDriver using GeckoDriverManager
    # driver = webdriver.Firefox(service=service, options=firefox_options)
    df1 = pd.read_csv(csv_file_path)
    df1['Date'] = df1['Date'].apply(convert_date)
    df1 = df1.sort_values(by='Date', ascending=True)
    from_date = df1.iloc[-1]["Date"]
    till_company=df1.iloc[-1]["Company"]
    till_analyst=df1.iloc[-1]["Analyst"]
    #dfm=pd.read_csv(r'E:\python\CompanyMasterUpdate.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    path_needed=os.path.join(parent_dir,'csv_data','CompanyMasterUpdate.csv')
    dfm=pd.read_csv(path_needed)
    dfm.set_index('Company', inplace=True)
    dfm=dfm.transpose()
    dict1=dfm.to_dict()
    #print(dict1)

    driver.get(url)
    time.sleep(2)

    go_on = True
    while go_on:
        go_on, df = keep(till_company,till_analyst,csv_file_path, from_date, df, driver,dict1)
        if not go_on:
            break
        if not click_load_more(driver):
            time.sleep(2)
            if not click_load_more(driver):
                time.sleep(5)
                if not click_load_more(driver):
                    break

    df.to_csv(csv_file_path, mode='a', header=False, index=False)
    driver.quit()
    return




def historicData():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    csv_file_path=os.path.join(parent_dir,'csv_data','HistoricDataFrom2018.csv')
    company_master_path=os.path.join(parent_dir,'csv_data','HistoricDataFrom2018.csv')
    #dfsu=pd.read_csv(r'E:\python\CompanyMasterUpdate.csv')
    dfsu=pd.read_csv(company_master_path)
    #csv_file_path = r'E:\python\HistoricDataFrom2018.csv'
    count =0
    df1=pd.read_csv(csv_file_path)
    from_date = str(convert_date(df1.iloc[-1]['Date'])+datetime.timedelta(days=1))
    if convert_date(from_date) <datetime.date.today():
        for com,lname, ticker_symbol,x in zip(dfsu["Company"],dfsu["Long Name"],dfsu["Ticker"],dfsu["to be taken"]):
            
            if x!=0:
                count+=1
                print(count)
                ticker_symbol_nse = str(ticker_symbol)
                stock_data = yf.download(ticker_symbol_nse, start=from_date)
                if not stock_data.empty:
                    stock_data['Company'] = com
                    stock_data['Long Name'] =lname
                    stock_data['Ticker']=ticker_symbol
                    stock_data.reset_index(inplace=True)
                    stock_data.to_csv(csv_file_path, mode='a', header=False, index=False)
                    print(f'Successfully appended {len(stock_data)} rows for {lname} ')
    return
UpdateCalls()
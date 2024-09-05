from flask import Flask, render_template, request, session, redirect, url_for, jsonify, redirect,flash
from main import load_data, process_data, sort_data_frame, hot_stocks_backend,recommended_stocks,rankgen,return_ltp,portfolio_updates
from util import convert_date, format_numbers_to_indian_system
import pandas as pd
import datetime
import plotly.graph_objs as go
import urllib.parse
import io
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,login_user,LoginManager,login_required,logout_user,current_user
from werkzeug.security import generate_password_hash,check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField, PasswordField,BooleanField,ValidationError
from wtforms.validators import DataRequired,EqualTo,Length
import os
import csv
from flask_dance.contrib.google import make_google_blueprint, google
from update import UpdateCalls,historicData
import time

app = Flask(__name__)

#User database
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.sqlite3' 

app.secret_key = 'koinahibtayega'  # Needed to encrypt session data

db = SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))

#User Databse Model
class users(db.Model,UserMixin):
    _id =db.Column("id",db.Integer,primary_key=True)
    name=db.Column(db.String(200),nullable =False)
    username=db.Column(db.String(20),unique=True,nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password_hash=db.Column(db.String(128))


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)
    
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def get_id(self):
        return self._id
    

# WTForms classes for Login and signup
class LogInForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    password_hash= PasswordField('Password',validators=[DataRequired()])

    submit = SubmitField("Submit")
class SignUpForm(FlaskForm):
    name=StringField("Name",validators=[DataRequired()])
    username=StringField("Username",validators=[DataRequired()])
    email=StringField("Email",validators=[DataRequired()])
    password_hash=PasswordField('Password',validators=[DataRequired(),EqualTo('password_hash2',message='Passwords must match!')])
    password_hash2=PasswordField('Confirm Password',validators=[DataRequired()])
    submit = SubmitField("Sign Up")

# Flask route for signup
@app.route('/signup',methods=['GET','POST'])
def signup():
    name = None
    form = SignUpForm()
     
    if form.validate_on_submit():
        user = users.query.filter_by(username=form.username.data).first()
        if user is None:
            # if no such username exists already, check if email exists
            user = users.query.filter_by(email=form.email.data).first()
            if user is None:
                # if no such email is present already create DB entry
                hashed_pwd=generate_password_hash(form.password_hash.data)
                user=users(name=form.name.data,email=form.email.data,username=form.username.data,password_hash=hashed_pwd)
                db.session.add(user)
                db.session.commit()
                # create user directory inside csv_data and add the needed CSV files
                current_dir = os.path.dirname(os.path.abspath(__file__)) 
                parent_dir = os.path.dirname(current_dir)
                dir_to_be_used=os.path.join(parent_dir,'csv_data')
                user_dir = f'User{user._id}csv_data'
                dir_to_create = os.path.join(dir_to_be_used, user_dir) 

                # Create the directory if it doesn't exist
                if not os.path.exists(dir_to_create):
                    os.makedirs(dir_to_create)

                    # Create CSV files with headers
                    stocks_portfolio_csv = os.path.join(dir_to_create, 'StocksPortfolio.csv')
                    history_orders_csv = os.path.join(dir_to_create, 'HistoryOrders.csv')
                    tracking_stocks_csv = os.path.join(dir_to_create, 'TrackingStocks.csv')

                    # Write headers to CSV files
                    with open(stocks_portfolio_csv, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Company', 'Bought Date', 'Price Bought At', 'Target', 'Upside', 'Quantity'])

                    with open(history_orders_csv, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Date', 'Action', 'Company', 'Product', 'Quantity', 'Price'])

                    with open(tracking_stocks_csv, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Company', 'Buy Date', 'Sell Date', 'Target', 'Buy Price', 'Sell Price', 'Quantity', 'Received Return'])

                    flash('User added successfully and directory with CSV files created.','success')
                flash('User Added successfully','success')
                print('User Added successfully')
                return redirect(url_for('login'))
            else:
                flash('Email already exists', 'danger')
                print('Email already exists')
        else:
            flash('Username already exists', 'danger')
            print('Username already exists')

    return render_template('signup.html',form=form,name=name)

#Login route
@app.route('/login',methods=['GET','POST'])
def login():
    
    form = LogInForm()
    if form.validate_on_submit():
        user = users.query.filter_by(username=form.username.data).first()
        if user and user.verify_password(form.password_hash.data):
            #login user
            login_user(user)

            #add u_id to session so that user specific csvs can be loaded
            session['user']=user._id
            flash('Login successful', 'success')
            print('Login successful')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            print('Invalid username or password')
    return render_template('login.html', form=form)

#Logout route
@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    session.clear()  
    logout_user()
    flash("You have been logged out successfully",'success')
    print('You have been logged out successfully')
    return(redirect(url_for('index')))

#To be used for google login, need to add the keys and all at top for it
@app.route('/login/google/authorized')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/plus/v1/people/me")
    assert resp.ok, resp.text
    user_info = resp.json()
    email = user_info["emails"][0]["value"]
    user = users.query.filter_by(email=email).first()
    if user is None:
        name = user_info["displayName"]
        base_username = email.split("@")[0]
        username = base_username
        count = 1
        while users.query.filter_by(username=username).first() is not None:
            username = f"{base_username}{count}"
            count += 1
        user = users(
            email=email,
            name=name,
            username=username,
        )
        db.session.add(user)
        db.session.commit()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        dir_to_be_used=os.path.join(parent_dir,'csv_data')
        user_dir = f'User{user._id}csv_data'
        dir_to_create = os.path.join(dir_to_be_used, user_dir)

        # Create the directory if it doesn't exist
        if not os.path.exists(dir_to_create):
            os.makedirs(dir_to_create)

            # Create CSV files with headers
            stocks_portfolio_csv = os.path.join(dir_to_create, 'StocksPortfolio.csv')
            history_orders_csv = os.path.join(dir_to_create, 'HistoryOrders.csv')
            tracking_stocks_csv = os.path.join(dir_to_create, 'TrackingStocks.csv')

            # Write headers to CSV files
            with open(stocks_portfolio_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Company', 'Bought Date', 'Price Bought At', 'Target', 'Upside', 'Quantity'])

            with open(history_orders_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Action', 'Company', 'Product', 'Quantity', 'Price'])

            with open(tracking_stocks_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Company', 'Buy Date', 'Sell Date', 'Target', 'Buy Price', 'Sell Price', 'Quantity', 'Received Return'])

        flash('User added successfully and directory with CSV files created.', 'success')
    login_user(user)
    session['user'] = user._id
    return redirect(url_for("dashboard"))


# Global definitions
# analyst rank dictionary to be used for easy access for ranks
analyst_rank={} 

#empty output dfs 
columns = ['Total Calls in Period: ', 'Total Successes in the period: ', 'Success %']
final_df = pd.DataFrame(columns=columns)
recommendation_df=pd.DataFrame(columns=columns)
rank_df=pd.DataFrame(columns=columns)
stocks_df=pd.DataFrame(columns=columns)
calls_df=pd.DataFrame(columns=columns)
history_df=pd.DataFrame(columns=columns)
form_values_rec={}

#unique companies list
unique_company={}

#calls that are processed in one go, used to display the modal content in analyst view
calls_to_be_processed= {}

rec_all_calls={}

#for hovering modal in analyst view
calls_by_company_stocks={}

#drop down options inside analyst view
dropdown_options = {
'period': ['1Y', '6M', '3M'],
    }

#drop down options for portfolio generation
dropdown_options_portfolio_gen={
}

# Default values for the form in analyst rank
date_to_be_considered =datetime.date.today()-datetime.timedelta(days=365)
default_form_values = {
    'start-date': '2018-01-01',
    'end-date': str(date_to_be_considered),
    'period': '1Y',
    'analyst': 'All'
}

#default values in hot stocks
default_form_values_stock={
    'start-date': '2018-01-01',
    'end-date': str(date_to_be_considered+datetime.timedelta(days=365)),
}

#default form values in recommendation
default_form_values_rec={
    'priority': 'Number of Recommendations',
    'period':'30D',
    'num':'All',
    'sort-by':'Final Factor',
    'rank-consider':'yes',
    'start-date': '2021-01-01',
    'end-date': str(date_to_be_considered),
    'period-considered': '1Y',
    'upside-factor-weight':'50%',
    'minimum-upside-current':'0%',
    'market-cap':'All'
}

#default form values in ranker
default_form_values_ranker={
    'start-date': '2021-01-01',
    'end-date': str(date_to_be_considered),
    'period-considered': '1Y'
}

#drop down options for recommendation page
dropdown_options_for_rec={
    'priority':['Number of Recommendations','Average Upside','Average Target','Max Upside','Max Target'],
    'period':['1D','5D','7D','15D','30D','120D'],
    'num':['5','10','20','30','All'],
    'sort-by':['Number of Recommendations','Average Upside','Average Target','Max Upside','Max Target','Norm Wt Num Calls','Norm Wt Avg Upside Curr','Final Factor','Max Upside Current','Average Upside Current'],
    'period-considered': ['1Y', '6M', '3M'],
    'weighted-options':['Weighted Target','Weighted Upside','Weighted Upside Current','Weighted Number of Calls'],
    'upside-factor-weight':['100%','90%','80%','70%','60%','50%','40%','30%','20%','10%','0%'],
    'minimum-upside-current':['0%','10%','15%','20%'],
    'market-cap':['0-500','500-2k','2k-5k','5k-20k','20k+','All']
}

#Home page route / default landing page route
@app.route('/')
def index():
    
    return render_template('index.html')

#first page after login
@app.route('/dashboard')
@login_required
def dashboard():
    global dropdown_options
    global stocks_track_path,history_orders_path,portfolio_path,company_list,l1, analyst_dfs, company_data,list_of_unique_analysts, calls_by_company, calls_df, dropdown_options,history_df
    global default_form_values,dropdown_options_portfolio_gen
    global final_df

    # columns = ['Total Calls in Period: ', 'Total Successes in the period: ', 'Success %']
    # final_df = pd.DataFrame(columns=columns)
    # recommendation_df=pd.DataFrame(columns=columns)
    # rank_df=pd.DataFrame(columns=columns)

    #update calls using webscraping from trendlyne
    UpdateCalls()

    #default Analyst view form values
    date_to_be_considered =datetime.date.today()-datetime.timedelta(days=365)
    default_form_values = {
    'start-date': '2018-01-01',
    'end-date': str(date_to_be_considered),
    'period': '1Y',
    'analyst': 'All'
    }

    #save user for accessing user specific directory and files
    user=session['user']

    #load all CSVs into dataframe and create dictionaries lists and even transfer paths for user specific CSVs
    stocks_track_path,history_orders_path,portfolio_path,company_list,l1, analyst_dfs, company_data,list_of_unique_analysts, calls_by_company, calls_df,history_df = load_data(user)
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date'])    
    dropdown_options['analyst']= list_of_unique_analysts
    dropdown_options_portfolio_gen['Company']=company_list
    session['form_values'] = default_form_values
    return render_template('dashboard.html',latest_calls_date=latest_calls_date,latest_yfinance=latest_yfinance)

#Force update data using the button on home page 
# @app.route('/update',methods=['POST'])
# @login_required
# def update():
#     historicData()
#     return redirect(url_for('dashboard'))

#analyst view
@app.route('/analyst',methods=['GET', 'POST'])
@login_required
def analyst():
    
    if 'form_values' not in session:
        session[form_values]= default_form_values
    
    global calls_to_be_processed
    global final_df
    global unique_company

    if request.method == 'POST':

        #request data from form
        form_values = {
            'start-date': request.form.get('start-date', default_form_values['start-date']),
            'end-date': request.form.get('end-date', default_form_values['end-date']),
            'period': request.form.get('period', default_form_values['period']),
            'analyst': request.form.get('analyst', default_form_values['analyst'])
        }
        session['form_values'] = form_values
    else:
        form_values = session['form_values']
    return render_template('analyst.html',df=final_df, form_values=form_values, dropdown_options=dropdown_options)

#generate df inside analyst_view
@app.route('/generate_data', methods=['POST'])
@login_required
def generate_data():
    global calls_to_be_processed
    global final_df
    global unique_company

    #pull values from form
    form_values = {
        'start-date': request.form['start-date'],
        'end-date': request.form['end-date'],
        'period': request.form['period'],
        'analyst': request.form['analyst']
    }
    session['form_values'] = form_values

    start_date = convert_date(form_values['start-date'])
    end_date = convert_date(form_values['end-date'])
    dur = form_values['period']
    analyst_to_be_displayed = form_values['analyst']

    #Process data
    final_df,calls_to_be_processed,unique_company = process_data(start_date, end_date, dur, analyst_to_be_displayed, l1, analyst_dfs, company_data)
    return render_template('analyst.html', df = final_df, form_values=form_values, dropdown_options=dropdown_options)

#sort the analyst df according to selected column
@app.route('/sort_table', methods=['POST'])
@login_required
def sort_table():
    global final_df
    if request.method == 'POST':
        sort_by = request.form['sort_by']
        if final_df is not None and len(final_df) > 1:
            final_df = sort_data_frame(final_df, sort_by)
        return render_template('analyst.html', df = final_df, form_values=session['form_values'], dropdown_options=dropdown_options)

# To return analyst wise calls to modal
@app.route('/get_analyst_details')
@login_required
def get_analyst_details():
    #request analyst name
    analyst = request.args.get('analyst')
    analyst = urllib.parse.unquote(analyst)

    
    if analyst in calls_to_be_processed:
        details_df = calls_to_be_processed[analyst].copy()
        if 'Remarks(if any)' in details_df.columns:
            details_df.drop(['Remarks(if any)'], axis=1,inplace=True)
        if 'To Be Taken'in details_df.columns:
            details_df.drop(['To Be Taken'], axis=1,inplace=True)
        details_df['Market Cap']=pd.to_numeric(details_df['Market Cap'],errors='coerce')
        details_df['Market Cap']=details_df['Market Cap']/(10**7)
        details_df['Target']=details_df['Target'].round(1)
        details_df=format_numbers_to_indian_system(details_df,['Market Cap'])
        details_df.reset_index(drop=True, inplace=True)
        details_html = details_df.to_html(classes='table table-striped')
        return jsonify({'html': details_html})
    return jsonify({'html': 'No details available for this analyst.'})

#To return analyst wise company summaries
@app.route('/get_analyst_company_details')
@login_required
def get_analyst_company_details():
    analyst = request.args.get('analyst')
    analyst = urllib.parse.unquote(analyst)
    if analyst in unique_company:
        details_df=unique_company[analyst]
        details_html=details_df.to_html(classes='inlay-table')

        #jsonify html so that hover modal can be used effectively
        return jsonify({'html': details_html})
    return jsonify({'html': 'No details available for this analyst.'})

#Stocks route
@app.route('/stocks')
@login_required
def stocks():
    global default_form_values_stock
    global stocks_df
    return render_template('stocks.html',df=stocks_df,form_values =default_form_values_stock)

#generate hot stocks df
@app.route('/generate_stocks_info',methods=['POST'])
@login_required
def generate_stocks_info():
    global stocks_df
    global calls_by_company_stocks

    #call form values
    form_values = {
        'start-date': request.form['start-date'],
        'end-date': request.form['end-date']
    }
    

    start_date = convert_date(form_values['start-date'])
    end_date = convert_date(form_values['end-date'])

    #process data
    stocks_df,calls_by_company_stocks=hot_stocks_backend(start_date,end_date,calls_by_company,l1)
    return render_template('stocks.html',df=stocks_df,form_values=form_values,)
    
#Stocks modal route
@app.route('/get_stocks_details')
@login_required
def get_stocks_details():
    global calls_by_company_stocks

    #get company whose detail has to be displayed
    company = request.args.get('company')
    company = urllib.parse.unquote(company)
    if company in calls_by_company_stocks:
        details_df=calls_by_company_stocks[company].copy()
        if 'Remarks(if any)' in details_df.columns:
            details_df.drop(['Remarks(if any)'], axis=1,inplace=True)
        if 'To Be Taken'in details_df.columns:
            details_df.drop(['To Be Taken'], axis=1,inplace=True)
        details_df['Market Cap']=pd.to_numeric(details_df['Market Cap'],errors='coerce')
        details_df['Market Cap']=details_df['Market Cap']/(10**7)
        details_df=format_numbers_to_indian_system(details_df,['Market Cap'])
        details_df=details_df.reset_index(drop=True)
        details_html=details_df.to_html(classes='table table-striped')
        return jsonify({'html': details_html})
    return jsonify({'html': 'No details available for this company.'})

#Recommendation flask route
@app.route('/recommendation')
@login_required
def recommendation():
    global recommendation_df, history_df, calls_df
    wtcon=True
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date']) 
    return render_template('recommendation.html',df=recommendation_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=default_form_values_rec,wtcon=wtcon, latest_yfinance=latest_yfinance, latest_calls_date=latest_calls_date)

#Generate recommendation 
@app.route('/generate_rec',methods=['POST'])
@login_required
def generate_rec():
    global rec_all_calls
    global dropdown_options_for_rec
    global default_form_values_rec
    global analyst_rank
    global analyst_dfs
    global company_data
    global recommendation_df
    global form_values_rec, calls_df, history_df
    form_values_rec={

        #'priority':request.form['priority'],
        'period':request.form['period'],
        'num':request.form['num'],
        'sort-by': request.form['sort-by'],
        'rank-consider':request.form.get('rank-consider','no'),
        'start-date':request.form['start-date'],
        'end-date':request.form['end-date'],
        'period-considered':request.form['period-considered'],
        'upside-factor-weight':request.form['upside-factor-weight'],
        'minimum-upside-current':request.form['minimum-upside-current'],
        'market-cap':request.form['market-cap']
    }

    #Update data
    # UpdateCalls()
    # historicData()
    # form values pull
    priority='Number of Recommendations'
    sort_by=form_values_rec['sort-by']
    period=form_values_rec['period']
    num = form_values_rec['num']
    rank_consider=form_values_rec['rank-consider']
    start_date=convert_date(form_values_rec['start-date'])
    end_date= convert_date(form_values_rec['end-date'])
    dur=form_values_rec['period-considered']
    upside_factor_weight=form_values_rec['upside-factor-weight']
    upside_filter=form_values_rec['minimum-upside-current']
    wtcon=True if rank_consider=="yes" else False
    mcap=form_values_rec['market-cap']
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date']) 
    recommendation_df,rec_all_calls=recommended_stocks(mcap,upside_filter,upside_factor_weight,start_date, end_date, dur, analyst_dfs, company_data,rank_consider,sort_by,priority,period,num,calls_df,l1,analyst_rank)

    #check if limited number of rows have to be displayed
    if num =='All':
        return render_template('recommendation.html',df=recommendation_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_calls_date=latest_calls_date, latest_yfinance=latest_yfinance)
    else:
        temp_df=recommendation_df.head(int(num))
        return render_template('recommendation.html',df=temp_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_calls_date=latest_calls_date, latest_yfinance=latest_yfinance)

 
#route for displaying calls in recommendation
@app.route('/get_stocks_details_for_rec')
@login_required
def get_stocks_details_for_rec():
    global rec_all_calls

    #request company name
    company = request.args.get('company')
    company = urllib.parse.unquote(company)
    if company in rec_all_calls:
        details_df=rec_all_calls[company].copy()
        if 'Remarks(if any)' in details_df.columns:
            details_df.drop(['Remarks(if any)'], axis=1,inplace=True)
        if 'To Be Taken'in details_df.columns:
            details_df.drop(['To Be Taken'], axis=1,inplace=True)
        if 'Market Cap' in details_df.columns:
            details_df.drop(['Market Cap'], axis=1,inplace=True)
        
        # details_df['Market Cap']=pd.to_numeric(details_df['Market Cap'],errors='coerce')
        # details_df['Market Cap']=details_df['Market Cap']/(10**7)
        # details_df=format_numbers_to_indian_system(details_df,['Market Cap'])
        details_html=details_df.to_html(classes='table table-striped')
        return jsonify({'html': details_html})
    return jsonify({'html': 'No details available for this company.'})

#route to generate the graphs in recommendation page using plotly
@app.route('/generate_stock_graph')
@login_required
def generate_stock_graph():

    #request company name
    company = request.args.get('company')
    company = urllib.parse.unquote(company)
    global rec_all_call
    #print(rec_all_calls)
    if company in rec_all_calls:
        #create copies
        df = rec_all_calls[company].copy()
        hdf = company_data[company].copy()
        
        #corresponds to the date since which the stock price data is shown
        first_call_date = df['Date'].min()
        today = datetime.date.today()
        to_be_plotted = hdf[(hdf['Date'] >= first_call_date) & (hdf['Date'] <= today)]

        #date list and close price list for plotting
        date_list = to_be_plotted['Date'].tolist()
        close_list = to_be_plotted['Close'].tolist()
        
        #plot
        trace = go.Scatter(x=date_list, y=close_list, mode='lines', name=f'Price for {company}')
        trace_horizontal_lines = []
        trace_markers = []
        analyst_colors = ['orange', 'green', 'red', 'black','purple']  
        for index, row in df.iterrows():
            color_index = index % len(analyst_colors)
            analyst_color = analyst_colors[color_index]
            trace_line = go.Scatter(x=date_list, y=[row['Target']] * len(date_list), mode='lines', 
                                    line=dict(color=analyst_color, dash='dash'), name=row['Analyst'])
            trace_horizontal_lines.append(trace_line)
            
            trace_marker = go.Scatter(x=[row['Date']], y=[row['Target']], mode='markers', 
                                      marker=dict(symbol='circle', size=10, color=analyst_color),
                                      name=f'Call by {row["Analyst"]} - {row["Upside"]}%')
            trace_markers.append(trace_marker)
        
        fig = go.Figure(data=[trace] + trace_horizontal_lines + trace_markers)
        fig.update_layout(title=f'Stock Prices for {company}', xaxis=dict(title='Date'), yaxis=dict(title='Price'))

        # Convert figure to JSON to send to frontend
        graph_json = fig.to_json()
        return jsonify({'graph': graph_json})
    
    return jsonify({'graph': ''})

#shows full table in recommendation page
@app.route('/show_full_table',methods=['POST'])
@login_required
def show_full_rec_table():
    global rec_all_calls
    global dropdown_options_for_rec
    global default_form_values_rec
    global analyst_rank
    global analyst_dfs
    global company_data
    global recommendation_df
    global form_values_rec, calls_df, history_df
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date']) 
    wtcon=True 
    return render_template('recommendation.html',df=recommendation_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_calls_date=latest_calls_date, latest_yfinance=latest_yfinance)

#sort recommendation df based on the column clicked (only available for 3-4 columns)
@app.route('/sort_recommendation_df')
@login_required
def sort_recommendation_df():
    global rec_all_calls
    global dropdown_options_for_rec
    global default_form_values_rec
    global analyst_rank
    global analyst_dfs
    global company_data
    global recommendation_df
    global form_values_rec, calls_df, history_df
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date']) 
    sort_by = request.args.get('sort_by')
    direction = request.args.get('direction', 'asc')
    wtcon =True
    if sort_by and not recommendation_df.empty:
        recommendation_df = recommendation_df.sort_values(by=sort_by, ascending=(direction == 'asc'))

    return render_template('recommendation.html', df=recommendation_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_yfinance=latest_yfinance, latest_calls_date=latest_calls_date)

# route to ranker page
@app.route('/ranker')
@login_required
def ranker():
    global rank_df
    return render_template('ranker.html',df=rank_df,dropdown_options_for_rec=dropdown_options_for_rec,form_values=default_form_values_ranker)

#generate rank route
@app.route('/generate_rank',methods=['POST'])
@login_required
def generate_rank():
    global analyst_rank
    global analyst_dfs
    global company_data
    global rank_df

    #pull form values
    form_values_rank={
        'start-date':request.form['start-date'],
        'end-date':request.form['end-date'],
        'period-considered':request.form['period-considered']
    }

    start_date=convert_date(form_values_rank['start-date'])
    end_date= convert_date(form_values_rank['end-date'])
    dur=form_values_rank['period-considered']
    dict1,rank_df,dict_df=rankgen(start_date, end_date, dur, analyst_dfs, company_data, l1,analyst_rank)
    df= pd.DataFrame(list(dict1.items()),columns=['Analyst','Score'])
    return render_template('ranker.html',df=rank_df,dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rank)

#route to portfolio 
@app.route('/portfolio')
@login_required
def portfolio():
    global dropdown_options_portfolio_gen,portfolio_path,stocks_track_path
    df=pd.read_csv(portfolio_path)

    #dictionary to add labels to portfolio references (should sell/buy/etc)
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #re rendering logic, update LTP current value check recommendations etc
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False

    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=(-3.0):
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#route taken by the buy button clicking in portfolio page
@app.route('/buy_from_portfolio',methods=['POST'])
@login_required
def buy_from_portfolio():
    global dropdown_options_portfolio_gen,portfolio_path,history_orders_path,stocks_track_path
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}
    company=request.form['company']
    target=request.form['target']
    date=datetime.date.today()
    ltp=request.form['price_buy']
    upside=round(((float(target)-float(ltp))/float(ltp))*100,2)
    qty=request.form['qty']
    df=pd.read_csv(portfolio_path)

    for index,row in df.iterrows():
        if row['Company']== company:
            print(row['Quantity'])
            ltp = round(((float(qty)*float(ltp))+(float(row['Quantity'])*float(row['Price Bought At'])))/(float(qty)+float(row['Quantity'])),2)
            qty = float(qty) +float(row['Quantity'])
            df=df.drop(index,axis='index')
    df.to_csv(portfolio_path, index=False)
    portfolio_data=pd.DataFrame([company,date,ltp,target,upside,qty]).transpose()
    portfolio_data.to_csv(portfolio_path, mode='a', header=False, index=False)
    orders_data=pd.DataFrame([date,'Buy',company,'CNC',qty,ltp]).transpose()
    orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#to upload CSV portfolio from my portfolio page route
@app.route('/add_csv_portfolio',methods=['POST'])
@login_required
def add_to_portfolio():
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

    global portfolio_path
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
   

   #file uploading logic
    if 'upload' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['upload']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        new_data = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
        existing_data = pd.read_csv(portfolio_path)

        if set(new_data.columns) == set(existing_data.columns):
            new_data.to_csv(portfolio_path, mode='a', header=False, index=False)
            for index,row in new_data.iterrows():
                    date=row['Bought Date']
                    company =row['Company']
                    qty=row['Quantity']
                    ltp=row['Price Bought At']
                    orders_data=pd.DataFrame([date,'Buy',company,'CNC',qty,ltp]).transpose()
                    orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)

            flash('File uploaded and data appended successfully.')
        else:
            flash('Column names do not match.')


        
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#Sell functionality from portfolio
@app.route('/sell_track_from_portfolio',methods=['POST'])
@login_required
def sell_track_from_portfolio():
    global history_orders_path,portfolio_path,stocks_track_path

    #pull details of the stock to be sold
    company = request.form['company']
    bought_date = request.form['bought_date']
    price_bought_at = request.form['price_bought_at']
    target = request.form['target']
    quantity = request.form['quantity']
    qty=request.form['qty']
    sold_on=datetime.date.today()
    sold_price=return_ltp(company)
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #adding to track df
    rcvd_return=round(((float(sold_price)-float(price_bought_at))/float(price_bought_at))*100,2)
    df = pd.read_csv(portfolio_path)
    for index,row in df.iterrows():
        if (float(row['Quantity'])==float(quantity)) and (row['Company'] == company) and (convert_date(row['Bought Date'])== convert_date(bought_date)) and ((float(row['Price Bought At'])) == (float(price_bought_at))) and ((float(row['Target']))== (float(target))):
            
            if float(qty)== float(quantity):
                df=df.drop(index,axis='index')
                orders_data=pd.DataFrame([sold_on,'Sell',company,'CNC',quantity,sold_price]).transpose()
                orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
                track_df=pd.DataFrame([company,bought_date,sold_on,target,price_bought_at,sold_price,qty,rcvd_return]).transpose()
                track_df.to_csv(stocks_track_path, mode='a', header=False, index=False)
            elif float(qty)<float(quantity):
                df.at[index,'Quantity']=float(quantity)-float(qty)
                orders_data=pd.DataFrame([sold_on,'Sell',company,'CNC',qty,sold_price]).transpose()
                orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
                track_df=pd.DataFrame([company,bought_date,sold_on,target,price_bought_at,sold_price,qty,rcvd_return]).transpose()
                track_df.to_csv(stocks_track_path, mode='a', header=False, index=False)
            else:
                flash('Cannot sell more than you own!','danger')

    
    # Save the updated DataFrame back to the CSV file
    df.to_csv(portfolio_path,index=False)

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#buy again from tracking df
@app.route('/buy_from_tracking_portfolio',methods=['POST'])
@login_required
def buy_from_tracking_portfolio():
    global stocks_track_path,portfolio_path,dropdown_options_portfolio_gen,history_orders_path
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #pulling buy form details
    company = request.form['company']
    target = request.form['target']
    bought_date = request.form['bought_date']
    sold_date=request.form['sold_date']
    price_bought_at = request.form['price_bought_at']
    quantity = request.form['qty']
    qty=request.form['quantity']
    date=datetime.date.today()
    ltp=request.form['price_buy']
    upside=round(((float(target)-float(ltp))/float(ltp))*100,2)
    df = pd.read_csv(portfolio_path)
    for index,row in df.iterrows():
        if row['Company']== company:
            print(row['Quantity'])
            ltp = round(((float(qty)*float(ltp))+(float(row['Quantity'])*float(row['Price Bought At'])))/(float(qty)+float(row['Quantity'])),2)
            qty = float(qty) +float(row['Quantity'])
            df=df.drop(index,axis='index')
    df.to_csv(portfolio_path, index=False)

    portfolio_data=pd.DataFrame([company,date,ltp,target,upside,quantity]).transpose()
    portfolio_data.to_csv(portfolio_path, mode='a', header=False, index=False)
    orders_data=pd.DataFrame([date,'Buy',company,'CNC',quantity,ltp]).transpose()
    orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
    df = pd.read_csv(stocks_track_path)
    # Filter the DataFrame to remove the specific row
    for index,row in df.iterrows():
        if (float(row['Quantity'])==float(qty)) and (convert_date(row['Sell Date'])== convert_date(sold_date)) and (row['Company'] == company) and (convert_date(row['Buy Date'])== convert_date(bought_date)) and ((float(row['Buy Price'])) == (float(price_bought_at))) and ((float(row['Target']))== (float(target))):
            
            df=df.drop(index,axis='index')
    
    # Save the updated DataFrame back to the CSV file
    df.to_csv(stocks_track_path,index=False)

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#delete from tracking portfolio table
@app.route('/delete_row', methods=['POST'])
@login_required
def delete_row():
    global stocks_track_path
    global dropdown_options_portfolio_gen ,portfolio_path
    recommendation_sell={}
    reason_recommendation={}
    recommendation_buy={}
    reason_buy={}

    #pull details from sell function
    company = request.form['company']
    bought_date = request.form['bought_date']
    sold_date=request.form['sold_date']
    price_bought_at = request.form['price_bought_at']
    target = request.form['target']
    quantity = request.form['quantity']
    # Load the DataFrame
    df = pd.read_csv(stocks_track_path)
    print(df)
    # Filter the DataFrame to remove the specific row
    for index,row in df.iterrows():
        if (float(row['Quantity'])==float(quantity)) and (convert_date(row['Sell Date'])== convert_date(sold_date)) and (row['Company'] == company) and (convert_date(row['Buy Date'])== convert_date(bought_date)) and ((float(row['Buy Price'])) == (float(price_bought_at))) and ((float(row['Target']))== (float(target))):
            
            df=df.drop(index,axis='index')
    
    # Save the updated DataFrame back to the CSV file
    df.to_csv(stocks_track_path,index=False)

    #re rendering logic, update LTP current value check recommendations etc
    df=pd.read_csv(portfolio_path)
    c_val=[]
    ltp_list=[]
    pl_list=[]
    remaining_up_list=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        curr_val=ltp*float(row['Quantity'])
        pl=((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100
        rem_up=((float(row['Target'])-float(ltp))/float(ltp))*100
        c_val.append(round(curr_val,2))
        ltp_list.append((ltp))
        pl_list.append(round(pl,2))
        remaining_up_list.append(round(rem_up,2))
        company=row['Company']
        if pl>=10.0:
            recommendation_sell[row['Company']]=True
            reason_recommendation[row['Company']]=f"Recieved {round(pl,2)}% returns already, sell {company} and buy again"
        else:
            recommendation_sell[row['Company']]=False
    df['Current Value']=c_val
    df['LTP']=ltp_list
    df['P/L %']=pl_list
    df['Remaining Upside']=remaining_up_list
    track_df=pd.read_csv(stocks_track_path)
    ltp_list1=[]
    current_return=[]
    for index,row in track_df.iterrows():
        ltp=return_ltp(row['Company'])
        ltp_list1.append((ltp))
        curr=round(((float(row['Target'])-float(ltp))/float(ltp))*100,2)
        current_return.append(curr)
        downside=round(((float(ltp)-float(row['Sell Price']))/float(row['Sell Price']))*100,2)
        if downside<=-3.0:
            recommendation_buy[row['Company']]=True
            reason_buy[row['Company']]=f"Stock dipped {downside}% from sell price, should buy now"
        else:
            recommendation_buy[row['Company']]=False
    track_df['LTP']=ltp_list1
    track_df['Current Return']=current_return
        
    
    return render_template('portfolio.html',df=df,track_df=track_df,recommendation_buy=recommendation_buy,reason_buy=reason_buy,recommendation_sell=recommendation_sell,reason_recommendation=reason_recommendation,dropdown_options=dropdown_options_portfolio_gen)

#Buy stock from recommendation page
@app.route('/add_to_portfolio_from_rec',methods=['POST'])
@login_required
def add_to_portfolio_from_rec():
    global portfolio_path
    company=request.form['company']
    target=request.form['target']
    date=datetime.date.today()
    bought_at=request.form['price_buy']
    upside=request.form['upside']
    qty=request.form['qty']
    df = pd.read_csv(portfolio_path)
    for index,row in df.iterrows():
        if row['Company']== company:
            print(row['Quantity'])
            bought_at = round(((float(qty)*float(bought_at))+(float(row['Quantity'])*float(row['Price Bought At'])))/(float(qty)+float(row['Quantity'])),2)
            qty = float(qty) +float(row['Quantity'])
            df=df.drop(index,axis='index')
    df.to_csv(portfolio_path, index=False)

    portfolio_data=pd.DataFrame([company,date,bought_at,target,upside,qty]).transpose()
    portfolio_data.to_csv(portfolio_path, mode='a', header=False, index=False)
    orders_data=pd.DataFrame([date,'Buy',company,'CNC',qty,bought_at]).transpose()
    orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
    global rec_all_calls
    global dropdown_options_for_rec
    global default_form_values_rec
    global analyst_rank
    global analyst_dfs
    global company_data
    global recommendation_df
    global form_values_rec, history_df, calls_df

    
    num = form_values_rec['num']
    rank_consider=form_values_rec['rank-consider']
    latest_calls_date=max(calls_df['Date'])
    latest_yfinance=max(history_df['Date'])
    wtcon=True if rank_consider=="yes" else False
    #recommendation_df,rec_all_calls=recommended_stocks(mcap,upside_filter,upside_factor_weight,start_date, end_date, dur, analyst_dfs, company_data,rank_consider,sort_by,priority,period,num,calls_df,l1,analyst_rank)
    if num =='All':
        return render_template('recommendation.html',df=recommendation_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_calls_date=latest_calls_date, latest_yfinance=latest_yfinance)
    else:
        temp_df=recommendation_df.head(int(num))
        return render_template('recommendation.html',df=temp_df, dropdown_options_for_rec=dropdown_options_for_rec,form_values=form_values_rec,wtcon=wtcon, latest_calls_date=latest_calls_date, latest_yfinance=latest_yfinance)

#Today updates route
@app.route('/today')
@login_required
def today():
    df=portfolio_updates(portfolio_path)
    return render_template('today.html',df=df)

#historic orders route
@app.route('/orders')
@login_required
def orders():
    global history_orders_path
    df=pd.read_csv(history_orders_path)
    LTP=[]
    status=[]
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        LTP.append(ltp)
        status.append('Executed')
    df['LTP']=LTP
    df['Status']=status
    return render_template('orders.html',df=df)
    
#Today's action route
@app.route('/actions')
@login_required
def actions():
    global dropdown_options_portfolio_gen,portfolio_path,stocks_track_path
    columns=['Company','Quantity']
    company=[]
    quantity=[]
    ltp_list=[]
    price=[]
    target=[]
    buy =[]
    sell=[]
    curr_pl=[]
    date=[]
    df=pd.read_csv(portfolio_path)
    df_actions=pd.DataFrame(columns=columns)
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        pl=round(((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100,2)
        
        #Recommendation to sell if profit >5
        if pl >5.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(False)
            sell.append(True)
            curr_pl.append(pl)
            date.append(row['Bought Date'])
        elif pl <0.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(True)
            sell.append(False)
            curr_pl.append(pl)
            date.append(row['Bought Date'])

    df_actions['Company']=company
    df_actions['Quantity']=quantity
    df_actions['LTP']=ltp
    df_actions['Price']=price
    df_actions['Target']=target
    df_actions['P&L']=curr_pl
    df_actions['Buy']=buy
    df_actions['Sell']=sell
    df_actions['Bought Date']=date

    return render_template('actions.html',df=df_actions)


#buy action from todays action page
@app.route('/buy_action',methods=['POST'])
@login_required
def buy_action():
    global dropdown_options_portfolio_gen,portfolio_path,stocks_track_path

    company=request.form['company']
    target=request.form['target']
    date=datetime.date.today()
    ltp=request.form['price_buy']
    upside=round(((float(target)-float(ltp))/float(ltp))*100,2)
    qty=request.form['qty']
    df = pd.read_csv(portfolio_path)
    for index,row in df.iterrows():
        if row['Company']== company:
            print(row['Quantity'])
            ltp = round(((float(qty)*float(ltp))+(float(row['Quantity'])*float(row['Price Bought At'])))/(float(qty)+float(row['Quantity'])),2)
            qty = float(qty) +float(row['Quantity'])
            df=df.drop(index,axis='index')
    df.to_csv(portfolio_path, index=False)
    portfolio_data=pd.DataFrame([company,date,ltp,target,upside,qty]).transpose()
    portfolio_data.to_csv(portfolio_path, mode='a', header=False, index=False)
    orders_data=pd.DataFrame([date,'Buy',company,'CNC',qty,ltp]).transpose()
    orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
    
    columns=['Company','Quantity']
    company=[]
    quantity=[]
    ltp_list=[]
    price=[]
    target=[]
    buy =[]
    sell=[]
    curr_pl=[]
    date=[]
    df=pd.read_csv(portfolio_path)
    df_actions=pd.DataFrame(columns=columns)
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        print(ltp)
        pl=round(((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100,2)
        if pl >5.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(False)
            sell.append(True)
            curr_pl.append(pl)
            date.append(row['Bought Date'])
        elif pl <0.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(True)
            sell.append(False)
            curr_pl.append(pl)
            date.append(row['Bought Date'])
    print(ltp_list)
    df_actions['Company']=company
    df_actions['Quantity']=quantity
    df_actions['LTP']=ltp_list
    df_actions['Price']=price
    df_actions['Target']=target
    df_actions['P&L']=curr_pl
    df_actions['Buy']=buy
    df_actions['Sell']=sell
    df_actions['Bought Date']=date

    return render_template('actions.html',df=df_actions) 

#sell from todays action
@app.route('/sell_action',methods=['POST'])
@login_required
def sell_action():
    global dropdown_options_portfolio_gen,portfolio_path,stocks_track_path

    company = request.form['company']
    bought_date = request.form['bought_date']
    price_bought_at = request.form['price_bought_at']
    target = request.form['target']
    quantity = request.form['quantity']
    qty=request.form['qty']
    sold_on=datetime.date.today()
    sold_price=return_ltp(company)
    rcvd_return=round(((float(sold_price)-float(price_bought_at))/float(price_bought_at))*100,2)
    df = pd.read_csv(portfolio_path)
    for index,row in df.iterrows():
        print(row['Quantity'])
        if (float(row['Quantity'])==float(quantity)) and (row['Company'] == company) and (convert_date(row['Bought Date'])== convert_date(bought_date)) and ((float(row['Price Bought At'])) == (float(price_bought_at))) and ((float(row['Target']))== (float(target))):
            if float(qty)== float(quantity):
                df=df.drop(index,axis='index')
                orders_data=pd.DataFrame([sold_on,'Sell',company,'CNC',quantity,sold_price]).transpose()
                orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
                track_df=pd.DataFrame([company,bought_date,sold_on,target,price_bought_at,sold_price,qty,rcvd_return]).transpose()
                track_df.to_csv(stocks_track_path, mode='a', header=False, index=False)
            elif float(qty)<float(quantity):
                df.at[index,'Quantity']=float(quantity) -float(qty)
                orders_data=pd.DataFrame([sold_on,'Sell',company,'CNC',qty,sold_price]).transpose()
                orders_data.to_csv(history_orders_path, mode='a', header=False, index=False)
                track_df=pd.DataFrame([company,bought_date,sold_on,target,price_bought_at,sold_price,qty,rcvd_return]).transpose()
                track_df.to_csv(stocks_track_path, mode='a', header=False, index=False)
            else:
                flash('Cannot sell more than you own!','danger')
    
    df.to_csv(portfolio_path,index=False)

    columns=['Company','Quantity']
    company=[]
    quantity=[]
    ltp_list=[]
    price=[]
    target=[]
    buy =[]
    sell=[]
    curr_pl=[]
    date=[]
    df=pd.read_csv(portfolio_path)
    df_actions=pd.DataFrame(columns=columns)
    for index,row in df.iterrows():
        ltp=return_ltp(row['Company'])
        pl=round(((float(ltp)-float(row['Price Bought At']))/float(row['Price Bought At']))*100,2)
        if pl >5.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(False)
            sell.append(True)
            curr_pl.append(pl)
            date.append(row['Bought Date'])
        elif pl <0.0:
            company.append(row['Company'])
            quantity.append(row['Quantity'])
            ltp_list.append(ltp)
            price.append(row['Price Bought At'])
            target.append(row['Target'])
            buy.append(True)
            sell.append(False)
            curr_pl.append(pl)
            date.append(row['Bought Date'])

    df_actions['Company']=company
    df_actions['Quantity']=quantity
    df_actions['LTP']=ltp_list
    df_actions['Price']=price
    df_actions['Target']=target
    df_actions['P&L']=curr_pl
    df_actions['Buy']=buy
    df_actions['Sell']=sell
    df_actions['Bought Date']=date

    return render_template('actions.html',df=df_actions)  
#reset session
@app.route('/reset_session')
def reset_session():
    session['form_values'] = default_form_values
    return redirect(url_for('index'))

if __name__ == "__main__":
    
    #app.run(ssl_context=('cert.pem', 'key.pem'),debug=True)
    app.run(debug=True)

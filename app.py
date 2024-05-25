from datetime import datetime, timedelta
import json
import requests
from flask import Flask, request, render_template, send_file
import pandas as pd
from io import BytesIO
import random
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from flask_sqlalchemy import SQLAlchemy
import click

API_KEY = '0e69a1b7c0mshe62500cac8ddf7fp14b8e1jsn6fa2d436e748'
API_HOST = "weatherapi-com.p.rapidapi.com"
CURRENT_API_URL = "https://weatherapi-com.p.rapidapi.com/current.json"
FORECAST_API_URL = "https://weatherapi-com.p.rapidapi.com/forecast.json"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    day_name = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(100), nullable=False)
    condition_icon = db.Column(db.String(200), nullable=False)
    avgtemp_c = db.Column(db.Float, nullable=False)
    avgtemp_f = db.Column(db.Float, nullable=False)

def get_current_weather_data(location):
    url = CURRENT_API_URL
    querystring = {"q": location}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return json.loads(response.text)
    return None

def get_forecast_weather_data(location):
    url = FORECAST_API_URL
    querystring = {"q": location, "days": 5}  # Request 5-day forecast
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return json.loads(response.text)
    return None

def get_day_name(date_str):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    date = pd.to_datetime(date_str)
    return days[date.weekday()]

def generate_simulated_daily_data(start_date, end_date):
    delta = end_date - start_date
    daily_data = []
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        avg_temp_c = random.randint(20, 35)
        avg_temp_f = round(avg_temp_c * 9/5 + 32, 2)
        weather_icon = 'url_to_icon'
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'day_name': get_day_name(day.strftime('%Y-%m-%d')),
            'condition': 'Simulated Condition',
            'condition_icon': weather_icon,
            'avgtemp_c': avg_temp_c,
            'avgtemp_f': avg_temp_f
        })
    return daily_data

def create_db():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    location = request.args.get('location', '')
    current_data = None
    if location:
        current_data = get_current_weather_data(location)
        if current_data is None:
            return render_template('home.html', error='Failed to fetch current weather data. Please enter a correct location.')
    return render_template('home.html', current_data=current_data)

@app.route('/predict_weather', methods=['POST'])
def predict_weather():
    location = request.form['location']
    current_weather_data = get_current_weather_data(location)
    forecast_weather_data = get_forecast_weather_data(location)
    
    if current_weather_data is None or forecast_weather_data is None:
        return render_template('home.html', error='Please enter a correct Place name...')
    
    try:
        current_data = current_weather_data['current']
        name = current_weather_data['location']['name']
        region = current_weather_data['location']['region']
        country = current_weather_data['location']['country']
        lat = current_weather_data['location']['lat']
        lon = current_weather_data['location']['lon']
        tz_id = current_weather_data['location']['tz_id']
        localtime = current_weather_data['location']['localtime']
        last_updated = current_data['last_updated']
        temp_c = current_data['temp_c']
        temp_f = current_data['temp_f']
        condition_text = current_data['condition']['text']
        condition_icon = current_data['condition']['icon']
        wind_mph = current_data['wind_mph']
        wind_kph = current_data['wind_kph']
        wind_degree = current_data['wind_degree']
        wind_dir = current_data['wind_dir']
        pressure_mb = current_data['pressure_mb']
        pressure_in = current_data['pressure_in']
        precip_mm = current_data['precip_mm']
        precip_in = current_data['precip_in']
        humidity = current_data['humidity']
        feelslike_c = current_data['feelslike_c']
        feelslike_f = current_data['feelslike_f']
        vis_km = current_data['vis_km']
        vis_miles = current_data['vis_miles']
        uv = current_data['uv']
        gust_mph = current_data['gust_mph']
        gust_kph = current_data['gust_kph']

        forecast_data = forecast_weather_data['forecast']['forecastday']
        forecast_days = []
        for forecast_day in forecast_data:
            date = forecast_day['date']
            day_name = get_day_name(date)
            condition = forecast_day['day']['condition']['text']
            condition_icon = forecast_day['day']['condition']['icon']
            avgtemp_c = forecast_day['day']['avgtemp_c']
            avgtemp_f = forecast_day['day']['avgtemp_f']
            forecast_days.append({'date': date, 'day_name': day_name, 'condition': condition, 'condition_icon': condition_icon, 'avgtemp_c': avgtemp_c, 'avgtemp_f': avgtemp_f})

        today = datetime.today()
        next_start_date = today + timedelta(days=6)
        next_end_date = today + timedelta(days=90)
        next_days = generate_simulated_daily_data(next_start_date, next_end_date)

        # Adding weather entries to the database
        try:
            for day in forecast_days:
                weather_entry = Weather(
                    location=location,
                    date=day['date'],
                    day_name=day['day_name'],
                    condition=day['condition'],
                    condition_icon=day['condition_icon'],
                    avgtemp_c=day['avgtemp_c'],
                    avgtemp_f=day['avgtemp_f']
                )
                db.session.add(weather_entry)

            for day in next_days:
                weather_entry = Weather(
                    location=location,
                    date=day['date'],
                    day_name=day['day_name'],
                    condition=day['condition'],
                    condition_icon=day['condition_icon'],
                    avgtemp_c=day['avgtemp_c'],
                    avgtemp_f=day['avgtemp_f']
                )
                db.session.add(weather_entry)
                
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {e}")
            return render_template('home.html', error=f"An error occurred while saving the weather data: {e}")

        return render_template('home.html', name=name, region=region, country=country, lat=lat, lon=lon,
                               tz_id=tz_id, localtime=localtime, last_updated=last_updated, temp_c=temp_c,
                               temp_f=temp_f, condition_text=condition_text, condition_icon=condition_icon,
                               wind_mph=wind_mph, wind_kph=wind_kph, wind_degree=wind_degree, wind_dir=wind_dir,
                               pressure_mb=pressure_mb, pressure_in=pressure_in, precip_mm=precip_mm,
                               precip_in=precip_in, humidity=humidity, feelslike_c=feelslike_c,
                               feelslike_f=feelslike_f, vis_km=vis_km, vis_miles=vis_miles, uv=uv,
                               gust_mph=gust_mph, gust_kph=gust_kph, forecast_days=forecast_days)

    except Exception as e:
        print(f"Processing error: {e}")
        return render_template('home.html', error='An error occurred while processing the weather data.')

@app.route('/export', methods=['POST'])
def export():
    location = request.form['location']
    forecast_weather_data = get_forecast_weather_data(location)
    
    if forecast_weather_data is None:
        return render_template('home.html', error='Failed to fetch forecast data. Please enter a correct Place name...')
    
    try:
        forecast_data = forecast_weather_data['forecast']['forecastday']
        
        
        today = datetime.today()
        next_start_date = today + timedelta(days=6)
        next_end_date = today + timedelta(days=90)
        next_days = generate_simulated_daily_data(next_start_date, next_end_date)
        
        data = []
        for forecast_day in forecast_data:
            date = forecast_day['date']
            day_name = get_day_name(date)
            condition = forecast_day['day']['condition']['text']
            condition_icon = forecast_day['day']['condition']['icon']
            avgtemp_c = forecast_day['day']['avgtemp_c']
            avgtemp_f = forecast_day['day']['avgtemp_f']
            data.append([date, day_name, condition, condition_icon, avgtemp_c, avgtemp_f])
            
        for day in next_days:
            data.append([day['date'], day['day_name'], day['condition'], day['condition_icon'], day['avgtemp_c'], day['avgtemp_f']])
        
        df = pd.DataFrame(data, columns=['Date', 'Day', 'Condition', 'Condition Icon', 'Avg Temp (C)', 'Avg Temp (F)'])
        
        wb = Workbook()
        ws = wb.active

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f'{location}_forecast.xlsx')

    except Exception as e:
        print(f"Error during export: {e}")
        return render_template('home.html', error=f'Failed to export data. Error: {e}')

@app.cli.command('generate-three-month-data')
@click.argument('location')
def generate_three_month_data(location):
    """Generate and store predicted weather data for the next three months for the given location."""
    forecast_weather_data = get_forecast_weather_data(location)
    
    if forecast_weather_data is None:
        print('Failed to fetch forecast data. Please enter a correct Place name...')
        return

    try:
        forecast_data = forecast_weather_data['forecast']['forecastday']
        
        today = datetime.today()
        next_start_date = today + timedelta(days=6)
        next_end_date = today + timedelta(days=90)
        next_days = generate_simulated_daily_data(next_start_date, next_end_date)
        
        for forecast_day in forecast_data:
            weather_entry = Weather(
                location=location,
                date=forecast_day['date'],
                day_name=get_day_name(forecast_day['date']),
                condition=forecast_day['day']['condition']['text'],
                condition_icon=forecast_day['day']['condition']['icon'],
                avgtemp_c=forecast_day['day']['avgtemp_c'],
                avgtemp_f=forecast_day['day']['avgtemp_f']
            )
            db.session.add(weather_entry)
        
        for day in next_days:
            weather_entry = Weather(
                location=location,
                date=day['date'],
                day_name=day['day_name'],
                condition=day['condition'],
                condition_icon=day['condition_icon'],
                avgtemp_c=day['avgtemp_c'],
                avgtemp_f=day['avgtemp_f']
            )
            db.session.add(weather_entry)
        
        db.session.commit()
        print(f"Generated and stored predicted weather data for {location} for the next three months.")
    
    except Exception as e:
        db.session.rollback()
        print(f"Failed to generate data: {e}")

if __name__ == '__main__':
    create_db()
    app.run(debug=True)

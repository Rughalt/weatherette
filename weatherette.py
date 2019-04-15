#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

# Copyright (c) 2019 Antoni Sobkowicz / Dragonshorn Studios
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import urllib.request
from threading import Timer
import rumps
import os
import json
import logging
import subprocess
from appscript import *
from rumps import separator, MenuItem


configs = {}
configs_data = {}
home_dir = os.path.expanduser('~')+'/.weatherette'
base_weather_url = "http://api.openweathermap.org/data/2.5/weather?id=%s&appid=%s&units=%s"
forecast_url = "http://api.openweathermap.org/data/2.5/forecast?id=%s&appid=%s&units=%s"

temp_base_text = {}
temp_base_text['metric'] = '%d℃'
temp_base_text['imperial'] = '%d℉'
wind_speed_text = {}
wind_speed_text['metric'] = 'm/s'
wind_speed_text['imperial'] = 'mph'


rumps.debug_mode(True)

if not os.path.exists(home_dir):
    os.makedirs(home_dir)

logging.basicConfig(filename=os.path.expanduser('~')+'/.weatherette/'+'app.log',level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')




class WeatheretteApp(rumps.App):
    apiKey = ''
    cityId = ''
    cityName = 'No city set'
    units = 'metric'

    def __init__(self):

        super(WeatheretteApp, self).__init__("Weatherette")

        if os.path.exists(home_dir + '/config.json'):
            config = json.load(open(home_dir + '/config.json'))
            self.apiKey = config['apiKey']
            self.cityId = config['cityId']
            self.cityName = config['cityName']
            self.units = config['units']
        self.save_config()

        self.menu = ['Weather description','Wind description',separator,"Forecast (next 9 hours)", "Forecast Data 1", "Forecast Data 2", "Forecast Data 3",separator,"City",separator,"Display","Preferences",separator,"About Weatherette"]
        self.icon = 'icons/01d.png'
        self.title = 'No data'
        self.template = True

        title_button = self.menu['City']
        title_button.title = self.cityName

        self.menu['Display'].add(MenuItem('Metric', callback=lambda sender: self.set_region('metric',sender)))
        self.menu['Display'].add(MenuItem('Imperial', callback=lambda sender: self.set_region('imperial',sender)))

        logging.info('Starting app')


    @rumps.clicked("About Weatherette")
    def about(self, _):
        window = rumps.alert(title='Weatherette', message='Simple weather app for your menu bar\nCopyright © 2019 Antoni Sobkowicz / Dragonshorn Studios', ok=None, cancel=None, icon_path='app_icon.png')
        window.run()
        pass

    @rumps.timer(600)
    def update_weather(self, _):
        logging.info('Current apiKey and cityId: %s,%s' % (self.apiKey, self.cityId))
        url = base_weather_url % (self.cityId, self.apiKey, self.units)
        logging.info(url)
        if self.apiKey == '' or self.cityId == '':
            result = rumps.alert('No API key or City id', 'Open Preferences to set API key or City id. You can get both from OpenWeatherMap.com. After you set them in preferences, restart the app!', ok="Open Preferences", other='Go to OpenWeatherMap', icon_path='app_icon.png')
            if result == 1:
                subprocess.Popen(["open", "-t", home_dir + '/config.json'])
            else:
                subprocess.Popen(["open", 'https://openweathermap.com'])
            return
        try:
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            data = json.loads(response.read())
            self.icon = 'icons/'+data['weather'][0]['icon']+'.png'
            title_button = self.menu['Weather description']
            title_button.title = data['weather'][0]['main'] + " (" + data['weather'][0]['description'] + ")"
            title_button = self.menu['Wind description']
            title_button.title = 'Wind: %s%s %s' % (data['wind']['speed'],wind_speed_text[self.units], degree_to_direction(data['wind']['speed']))
            title_button = self.menu['City']
            title_button.title = data['name']
            self.title = temp_base_text[self.units] % data['main']['temp']

            url = forecast_url % (self.cityId, self.apiKey, self.units)
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            data = json.loads(response.read())
            forecast_id = 0
            for forecast in data['list'][:3]:
                forecast_id += 1
                forecast_button = self.menu['Forecast Data %s' % forecast_id]
                forecast_button.icon = 'icons/'+forecast['weather'][0]['icon']+'.png'
                forecast_button.template = True
                forecasted_temp = temp_base_text[self.units] % forecast['main']['temp'] + " " + forecast['weather'][0]['main'] + " (" + forecast['weather'][0]['description'] + ")"
                forecast_button.title = forecasted_temp
        except Exception as e:
            result = rumps.alert('Problem with accessing OpenWeatherMap',
                                 'Weatherette had problem with connecting OpenWeatherMap. Check if you API key is correct and the site is online!',
                                 ok="Close", other='Go to OpenWeatherMap', icon_path='app_icon.png')
            logging.exception('message')

        pass

    @rumps.notifications
    def notification_center(info):
        print('a')
        if 'preferences' in info:
            subprocess.Popen(["open", "-t", home_dir + '/config.json'])


    def set_region(self,name,menu):
        self.units = name

        self.update_weather(None)
        self.save_config()
        pass

    def save_config(self):
        config = {'apiKey': self.apiKey, 'cityId': self.cityId, 'cityName': self.cityName, 'units': self.units}
        json.dump(config, open(home_dir + '/config.json','w'))

        logging.info('Saved configuration data')
        pass

    @rumps.clicked("Preferences")
    def set_city(self, _):
        subprocess.Popen(["open", "-t", home_dir + '/config.json'])




def degree_to_direction(degrees):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((degrees + 11.25) / 22.5)
    return dirs[ix % 16]

if __name__ == "__main__":
    WeatheretteApp().run()
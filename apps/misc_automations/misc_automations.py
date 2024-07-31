import appdaemon.plugins.hass.hassapi as hass

import csv
import os
import sys
import globals_module as globals

from datetime import date, datetime, time
from requests import Session
from geopy.geocoders import Nominatim

class MiscAutomations(hass.Hass):
  
  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)

    # Setup some variables:
    self.sab_api_uri = globals.sabnzbd_url + "/sabnzbd/api?apikey=" + globals.sabnzbd_api_key + "&output=json"
    self.sab_pause_and_resume = "&mode=config&name=set_pause&value="
    self.sab_pause_duration_in_minutes = 930

    # Load external AppDaemon libraries:
    self.function_library = self.get_app("function_library")

    # Startup sanity checks:
    self.run_in(self.on_weather_change_cb, 1)
    self.run_in(self.setup_working_day, 1)
    direction = self.function_library.get_wind_direction()
    self.set_state(globals.wind_direction_sensor, state = direction, attributes = {"friendly_name": "Wind Direction"})

    
    # Time based tasks:
    setup_working_day = self.run_daily(self.setup_working_day, "00:00:01")
    reset_rain_switch = self.run_daily(self.run_at_midnight_tasks, "00:00:02")
    pause_sabnzbd = self.run_daily(self.on_pause_sabnzbd_during_the_day, "07:30:00")

    # State Monitors:
    self.listen_state(self.on_weather_change, globals.weather)
    self.listen_state(self.on_thunderstorm_nearby, "sensor.blitzortung_lightning_distance", old = "unknown")
    self.listen_state(self.on_wind_direction_change, globals.wind_bearing)
    self.listen_state(self.on_hub_power_switched_off, globals.draytek_router_power, old = "on", new = "off", duration = "30")
    self.listen_state(self.on_hub_power_switched_off, globals.unifi_main_switch_power, old = "on", new = "off", duration = "30")

    # Event Monitors:
    self.listen_event(self.on_telegram_text_received, entity_id = globals.telegram_input_text_message, domain = "input_text")

    
  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################
  def on_telegram_text_received(self, event_name, data, cb_args):
    if event_name == "call_service":
      text_entity_id, text_contents = self.function_library.input_text_event(data["service_data"])
      if text_entity_id == globals.telegram_input_text_message:
        self.call_service(globals.max_telegram, title = "HA Web frontend message.", message = text_contents)

  def on_weather_change(self, entity, attribute, old, new, cbargs):
    if old not in ["unknown", "unavailable"]:
      self.run_in(self.on_weather_change_cb, 1)

  def on_thunderstorm_nearby(self, entity, attribute, old, new, cb_args):
    self.log("Thunderstorm.")
    if new != "unavailable":
      phone_app_dnd = "sensor." + globals.max_phone + "_do_not_disturb_sensor"
      distance_in_miles = float(new) * 0.62137119
      if distance_in_miles < 30:
        self.log("Thunderstorm detected nearby.")
        if self.get_state(phone_app_dnd) != "off":
          self.call_service(globals.max_app, title = "Thunderstorm nearby.",\
                                             message = "There is a thunderstorm " + str(distance_in_miles) + " miles away.",\
                                             data = {"channel": globals.weather_channel,\
                                                     "media_stream": "alarm_stream",\
                                                     "tts_text": "There is a thunderstorm nearby.",\
                                                    })
    

  def run_at_midnight_tasks(self, cb_args):
    self.log("Reset rain sensor.")
    self.turn_off(globals.has_it_rained_today_switch)
  
  def setup_working_day(self, cb_args):
    # This requires a on_working_days.csv file for non-working days (see included).
    # This needs error checking for the csv file.
    #
    #self.log("Check working day.")
    today_state = "on"
    tomorrow_state = "on"
    working_day_today_sensor = "sensor.working_day_today"
    working_day_tomorrow_sensor = "sensor.working_day_tomorrow"
    current_date = date.today()
    current_day = date.today().weekday()
    #self.log("Day: " + str(current_day))
    #today_state = self.get_state(working_day_today_sensor)
    #self.log("today_state: " + str(today_state))
    #tomorrow_state = self.get_state(working_day_tomorrow_sensor)
    with open('/config/appdaemon/apps/misc_automations/non_working_days.csv') as csv_file:
      working_day_reader = csv.reader(csv_file, delimiter = ',')
      line_count = 0
      for row in working_day_reader:
        if line_count == 0:
            pass
        else:
            check_date = date(int(row[3]), int(row[2]), int(row[1]))
            delta = current_date - check_date
            #self.log(delta.days)
            if delta.days == 0 and current_day < 6:
              self.log("Today is a bank holiday.")
              # Tomorrow sensor on.
              tomorrow_state = "on"
              # Today sensor on.
              today_state = "off"
            elif delta.days == 1 and current_day < 6:
              self.log("Bank holiday has passed. Today is a normal day")
              # Today sensor on.
              today_state = "on"
            elif current_day > 5:
              self.log("It is the weekend.")
              # Today sensor off.
              today_state = "off"
            elif current_day == 4 or current_day == 5: # It is Friday or Saturday.
              tomorrow_state = "off"
            if delta.days == -1:
              self.log("Tomorrow is a bank holiday.")
              # Tomorrow sensor off.
              tomorrow_state = "off"
        line_count += 1
    self.set_state(working_day_tomorrow_sensor, state = tomorrow_state, attributes = {"friendly_name": "Working Day Tomorrow Sensor"})
    self.set_state(working_day_today_sensor, state = today_state, attributes = {"friendly_name": "Working Day Today Sensor"})
  
  def on_wind_direction_change(self, entity, attribute, old, new, cb_args):
    direction = self.function_library.get_wind_direction()
    self.log("Wind direction: " + str(direction))
    self.set_state(globals.wind_direction_sensor, state = direction, attributes = {"friendly_name": "Wind Direction"})
  
  def on_weather_change_cb(self, cb_args):
    bad_weather_conditions = ["rain", "pour", "pouring", "drizzle"]
    current_condition = self.get_state(globals.weather)
    if current_condition in bad_weather_conditions:
        self.log("It has been raining.")
        self.turn_on(globals.has_it_rained_today_switch)

  def on_hub_power_switched_off(self, entity, attribute, old, new, kwargs):
    power_entity = entity
    self.log("Power switched off for 30 seconds: " + str(power_entity))
    self.log("Powering back on.")
    self.turn_on(power_entity)

  def on_pause_sabnzbd_during_the_day(self, cb_args):
    self.log("Pausing SabNZBD for: " + str(self.sab_pause_duration_in_minutes) + " minutes.")
    api_resume = self.sab_pause_and_resume + str(self.sab_pause_duration_in_minutes)
    uri = self.sab_api_uri + api_resume
    self.pause_and_set_sabnzbd_resume_time(uri)

  
  ###############################################################################################################
  # Other functions:
  ###############################################################################################################
  
  def pause_and_resume_sabnzbd_at(self, resume_at_time):
    today = date.today()
    resume_time_hours = datetime.strptime(resume_at_time,"%H%M").time()
    resume_time = datetime.combine(today,resume_time_hours)
    time_now = datetime.now()
    diff = resume_time - time_now
    difference_in_minutes = diff.total_seconds() /60
    number_of_minutes = str(difference_in_minutes).split(".")
    api_resume = self.sab_pause_and_resume + str(number_of_minutes[0])
    uri = self.sab_api_uri + api_resume
    self.pause_and_set_sabnzbd_resume_time(uri)

  def pause_and_set_sabnzbd_resume_time(self, uri):
    api_response = True
    with Session() as s:
      try:
        response = s.get(uri)
        data = response.json()
        #self.log(data)
        if data["status"] == True:
          self.log("SabNZBD paused.")
      except:
        api_response = False
  
  def get_address_from_long_lat(self, longitude, latitude):
    current_location = (latitude, longitude)
    try:
      geolocator = Nominatim(user_agent = "appdaemon")
    except Exception:
      self.log("Unable to get street address.")
      address = "Unable to get street address."
    finally:
      address = geolocator.reverse(current_location)
    return address


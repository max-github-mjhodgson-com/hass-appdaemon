# Misc Automations Script.
#
# Automations that don't fit in anywhere else.
#
# 2024 Max Hodgson
# Version: 241107.01

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
    self.weather = globals.weather # Another temp fix until I can get a reliable weather API.
    
    self.travel_times_new = { "sensor.drive_from_home_to_work": { "default_travel_time": 20, 
                                                                  "car_location_id": globals.maxs_cars,
                                                                  "start_locations": ["Home", "Home_b"],
                                                                  "notification": "placeholder",
                                                                  "work_day_level": 0,
                                                                  "work_day_person": "max",
                                                                  "time_range_sensor": "binary_sensor.travel_time_test",
                                                                  "alert_sent": False,
                                                                  "enabled": True,
                                                                  "handler": ""
                                                                },
                              "sensor.drive_from_work_to_home": { "default_travel_time": 30,
                                                                  "car_location_id": globals.maxs_cars,
                                                                  "start_locations": ["zone.car_park_work"],
                                                                  "notification": "placeholder",
                                                                  "work_day_level": 0,
                                                                  "work_day_person": "max",
                                                                  "time_range_sensor": "binary_sensor.leave_for_work",
                                                                  "alert_sent": False,
                                                                  "enabled": True,
                                                                  "handler": ""
                                                                },
                              "sensor.drive_from_pbm_to_home":    { "default_travel_time": 30,
                                                                  "car_location_id": globals.maxs_cars,
                                                                  "start_locations": ["zone.pbm"],
                                                                  "notification": "placeholder",
                                                                  "work_day_level": 2,
                                                                  "work_day_person": "max",
                                                                  "time_range_sensor": "binary_sensor.travel_time_pbm_to_home",
                                                                  "alert_sent": False,
                                                                  "enabled": True,
                                                                  "handler": ""
                                                                },
                              "sensor.drive_from_home_to_pbm": { "default_travel_time": 30,
                                                                  "car_location_id": globals.maxs_cars,
                                                                  "start_locations": ["Home", "Home_b"],
                                                                  "notification": "placeholder",
                                                                  "work_day_level": 2,
                                                                  "work_day_person": "max",
                                                                  "time_range_sensor": "binary_sensor.travel_time_home_to_pbm",
                                                                  "alert_sent": False,
                                                                  "enabled": True,
                                                                  "handler": ""
                                                                }
                            }
    # Load external AppDaemon libraries:
    self.function_library = self.get_app("function_library")

    # Startup sanity checks:
    self.run_in(self.setup_working_day, 1)
    direction = self.function_library.get_wind_direction()
    self.set_state(globals.wind_direction_sensor, state = direction, attributes = {"friendly_name": "Wind Direction"})
    
    # Time based tasks:
    self.run_daily(self.setup_working_day, "00:00:01")
    self.run_daily(self.run_at_midnight_tasks, "00:00:02")
    self.run_daily(self.on_pause_sabnzbd_during_the_day, "07:30:00")
    self.run_every(self.ping_devices, "now", 1*60, devices = globals.device_tracker_pings)

    # State Monitors:
    self.listen_state(self.on_weather_change, self.weather, immediate = True)
    self.listen_state(self.on_thunderstorm_nearby, "sensor.blitzortung_lightning_distance", old = "unknown")
    self.listen_state(self.on_wind_direction_change, globals.wind_bearing)
    self.listen_state(self.on_hub_power_switched_off, globals.draytek_router_power, old = "on", new = "off", duration = "30")
    self.listen_state(self.on_hub_power_switched_off, globals.unifi_main_switch_power, old = "on", new = "off", duration = "30")
    for travel_time_monitors in self.travel_times_new.keys():
      travel_time_enable = self.travel_times_new[travel_time_monitors]["enabled"]
      if travel_time_enable == True:
        self.log("Adding listen_state for: " + str(travel_time_monitors))
        self.travel_times_new[travel_time_monitors]["handler"] = self.listen_state(self.on_travel_time_delays, travel_time_monitors, immediate = True)
  
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

  def on_weather_change(self, entity, attribute, old, new, cb_args):
    if old not in ["unknown", "unavailable"]:
      self.log("Old: " + str(old))
      self.log("New: " + str(new))
      #self.run_in(self.on_weather_change_cb, 1)
      bad_weather_conditions = ["rain", "rainy", "pour", "pouring", "drizzle"]
      current_condition = self.get_state(self.weather)
      if current_condition in bad_weather_conditions:
        self.log("It has been raining.")
        self.turn_on(globals.has_it_rained_today_switch)

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
    with open(globals.non_working_days_csv_path) as csv_file:
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
    if self.function_library.debug():
      self.log("Wind direction: " + str(direction))
    self.set_state(globals.wind_direction_sensor, state = direction, attributes = {"friendly_name": "Wind Direction"})

  def on_hub_power_switched_off(self, entity, attribute, old, new, cb_args):
    power_entity = entity
    self.log("Power switched off for 30 seconds: " + str(power_entity))
    self.log("Powering back on.")
    self.turn_on(power_entity)

  def on_pause_sabnzbd_during_the_day(self, cb_args):
    self.log("Pausing SabNZBD for: " + str(self.sab_pause_duration_in_minutes) + " minutes.")
    api_resume = self.sab_pause_and_resume + str(self.sab_pause_duration_in_minutes)
    uri = self.sab_api_uri + api_resume
    self.pause_and_set_sabnzbd_resume_time(uri)

  # This utilises the Waze travel time integration within Home Assistant.
  # The integration returns a number of minutes for a specific route. If the number of minutes is above a threshold,
  # it will raise an mobile phone alert.
  # Each route has it's own notification flag, so as not to bombard the user with multiple alerts.
  # It will only alert when the car is in the start location and the time of day sensor is on
  # (e.g. will only alert if the time is applicable for the journey).
  # Can be used for multiple users.
  # 
  def on_travel_time_delays(self, entity, attribute, old, new, cb_args):
    if self.function_library.debug():
      self.log("Travel time change.")
      self.log("Travel time new: " +  str(entity) + ", " + str(new))
    if str(new) != "unavailable" and new != None:
      if self.function_library.debug():
        self.log("Travel time entity: " + str(entity) + " from: " + str(old) + " to: " + str(new))
      car_location = ""
      new_travel_time = int(new)
      if entity in self.travel_times_new.keys():
        travel_time = self.travel_times_new[entity]["time_range_sensor"]
        start_locations = self.travel_times_new[entity]["start_locations"]
        alert_sent = self.travel_times_new[entity]["alert_sent"]
        if self.get_state(travel_time) == "on":
          car_location_id = self.travel_times_new[entity]["car_location_id"]
          for car_location_tmp in car_location_id:
            car_location_state = self.get_state(car_location_tmp)
            if car_location_state in start_locations:
              car_location = car_location_state
              break
            else:
              continue
            self.log(car_location)
          work_day_level = self.travel_times_new[entity]["work_day_level"]
          work_day_person = self.travel_times_new[entity]["work_day_person"]
          working_day_return_code, working_day = self.function_library.is_it_a_work_day_today(work_day_person)
          if working_day_return_code == work_day_level and car_location in start_locations:
            travel_time_lookup = self.travel_times_new[entity]["default_travel_time"]
            if new_travel_time > travel_time_lookup:
              if alert_sent == False:
                self.travel_times_new[entity]["alert_sent"] = True
                friendly_name = self.get_state(entity, attribute = "friendly_name").lower()
                traffic_delays_text = "Travel time for " + friendly_name + " has delays. " + str(travel_time_lookup) + " minutes."
                self.log(traffic_delays_text)
                self.call_service(globals.max_telegram, title = "Traffic delays", message = traffic_delays_text)
                self.call_service(globals.max_app,  title = traffic_delays_text,\
                                                    message = "TTS",\
                                                    data = {"media_stream": "alarm_stream",\
                                                            "tts_text": "There are traffic delays."})
              else:
                self.log("Alert already sent (a).")
            if new_travel_time < travel_time_lookup:
              if alert_sent == True:
                self.log("Alert already sent (b).")
              self.travel_times_new[entity]["alert_sent"] = False
                
  
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

  def ping_devices(self, cb_args):
    #self.log("Ping devices.")
    devices = cb_args["devices"]
    #self.log(devices)
    for device in devices:
      #self.log(device)
      self.call_service("homeassistant/update_entity", entity_id = device)
      
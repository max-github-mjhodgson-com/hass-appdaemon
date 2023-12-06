# Function Library
#
# Version: 10052023.01
# Max Hodgson 2023
#
# Provides some global functions.
# These can be called from the other apps.
#
#
import appdaemon.plugins.hass.hassapi as hass
import globals_module as globals

from datetime import datetime


class FunctionLibrary(hass.Hass):

  def initialize(self):
    #self.log("Function Library Running.")
    pass

  def is_house_occupied(self):
    house_mode = self.get_state(globals.house_mode_selector)
    if house_mode in globals.house_not_occupied:
      return 0
    elif house_mode in globals.house_occupied:
      return 1
    elif house_mode in globals.house_sleep:
      return 2
      
  def is_car_at_home(self):
    where_is_car = self.get_state(globals.car_tracker)
    #self.log(where_is_car)
    if where_is_car in globals.car_home_locations:
      return 0
    else:
      return 1
  
  def are_we_asleep(self):
    # To do
    return 0
  
  def is_it_a_work_day_today(self, person):
    # This will check the personal calendar for the "person" for vacation.
    # To do: have options for a group.
    # Set default return codes.
    working_day_return_code = 0
    working_day="off"

    # Check the person's calendar.
    if self.get_state(globals.vacation_calendars[person]) == "on":  # On holiday (From work).
      working_day_return_code = 1
      working_day="off"
    elif self.get_state(globals.workday_sensor) == "off" or self.get_state("calendar.england_holidays") == "on":  # Weekend or Bank holiday.
      working_day_return_code = 2
      working_day="off"
    elif self.get_state(globals.away_calendars[person]) == "on":  # Away.
      working_day_return_code = 3
      working_day="off"
    else:  # Working.
      working_day_return_code = 0
      working_day="on"
    friendly_name = self.get_state("person." + str(person), attribute = "friendly_name")
    self.log("Friendly name: " + str(friendly_name))
    self.log("Person: " + str(person))
    self.set_state("sensor.working_day_" + str(person), state=working_day, attributes = {"friendly_name": "Working day for "+ str(friendly_name), "detail": None})
    return working_day_return_code, working_day

  def is_the_traffic_to_work_heavy(self):
    # To do
    # sensor.waze_car_park_test
    return 0
  
  def press_button(self, button):
    # To Do
    self.log("Button pressed.")

  def i_am_alive(self):
    self.log("I am alive.")
    
  def turn_off_alert(self, alert_entity_id):
    self.log("Turn off alert: " + str(alert_entity_id))
    self.call_service("alert/turn_off", alert_entity_id)

  def degrees_to_cardinal(self, d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    x = int((d/22.5)+.5)
    return dirs[x % 16]

  def get_wind_direction(self):
    wind_direction = self.degrees_to_cardinal(int(self.get_state(globals.wind_bearing)))
    return wind_direction
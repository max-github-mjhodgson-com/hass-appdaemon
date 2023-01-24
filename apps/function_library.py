# Provides some global functions.
# These can be called from the other apps.
#
# Max Hodgson 2023
#
import appdaemon.plugins.hass.hassapi as hass
import globals

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
    if globals.car_tracker == "home" or globals.car_tracker == "home_b":
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
    return_code = 0
    working_day="off"

    # Check the person's calendar.
    if self.get_state(globals.vacation_calendars[person]) == "on":
      working_day_return_code = 1
      working_day="off"
    if self.get_state(globals.workday_sensor) == "on" or self.get_state("calendar.england_holidays") == "on":
      working_day_return_code = 2
      working_day="off"
    if self.get_state(globals.away_calendars[person]) == "on":
      working_day_return_code = 3
      working_day="off"

    friendly_name = self.get_state("person."+ person, attribute = "friendly_name")
    self.set_state("sensor.non_working_day_"+person, state=working_day, attributes = {"friendly_name": "Non-working day for "+friendly_name, "detail": None})
    return working_day_return_code, working_day

  def is_the_traffic_to_work_heavy(self):
    # To do
    # sensor.waze_car_park_test
    return 0
  
  def press_button(self, button):
    # To Do
    self.log("Button pressed.")

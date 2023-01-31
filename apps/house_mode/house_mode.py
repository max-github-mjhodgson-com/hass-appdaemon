# Controls the mode that the house is in.
# 
# Needs an input_select configured in Home Assistant.
#
# Max Hodgson 2023
import appdaemon.plugins.hass.hassapi as hass
import globals
import time, datetime
from datetime import datetime


class House_Mode(hass.Hass):

  def initialize(self):
    self.log("=" * 30)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))

    # General function library:
    global FunctionLibrary
    FunctionLibrary = self.get_app("function_library")

    # Garage function library:
    global GarageLibrary
    GarageLibrary = self.get_app("garage")

    # Squeezebox Control Function Library:
    global SqueezeboxControl
    SqueezeboxControl = self.get_app("squeezebox_control")

    global MaxAutomationsLibrary
    MaxAutomationsLibrary = self.get_app("max_automations")

    FunctionLibrary.i_am_alive()
    return_code, work_day = FunctionLibrary.is_it_a_work_day_today("max")
    self.log(str(return_code) + str(work_day))

    self.listen_state(self.everyone_is_out, "group.persons", new="not_home", duration = 20)
    self.listen_state(self.someone_just_arrived_home, "group.persons", new="home", duration = 30)
    self.listen_state(self.house_mode_just_left_timeout, globals.house_mode_selector, new="Just Left", duration = 30)
    self.listen_state(self.house_mode_just_arrived_timeout, globals.house_mode_selector, new="Just Arrived", duration = 30)
    self.listen_state(self.execute_just_arrived_automations, globals.house_mode_selector, new="Just Arrived", old = "Out", duration = 10)
    self.listen_state(self.execute_just_left_automations, globals.house_mode_selector, new = "Just Left", old = "Home", duration = 10)
    self.listen_state(self.execute_pre_arrival_automations, globals.house_mode_selector, new = "Pre-Arrival", duration = 10)
    house_mode_change = self.listen_state(self.on_house_mode_change, globals.house_mode_selector)

###############################################################################################################
# Callback functions:
###############################################################################################################
  def everyone_is_out(self, entity, attribute, old, new, kwargs):
    self.log('The last person just left the house.')
    self.select_option(globals.house_mode_selector, "Just Left")
  
    
  def someone_just_arrived_home(self, entity, attribute, old, new, kwargs):
    self.log('Someone just arrived home.: ' + entity)
    self.log(attribute)
    self.select_option(globals.house_mode_selector, "Just Arrived")
    # Run any specific person automations.
    # Find out who by iterating the persons group and getting the state of each memmber.
    persons_at_home = self.get_state("group.persons", attribute = "entity")
    

  def house_mode_just_left_timeout(self, entity, attribute, old, new, kwargs):
    self.log('House Mode Just Left has timed out, switching to Out.')
    self.select_option(globals.house_mode_selector, "Out")
    
  def house_mode_just_arrived_timeout(self, entity, attribute, old, new, kwargs):
    self.log('House Mode Just Arrived has timed out, switching to Home.')
    self.select_option(globals.house_mode_selector, "Home")
  
  # Manuallly triggered pre-arrival.
  def execute_pre_arrival_automations(self, entity, attribute, old, new, kwargs):
    self.log("Pre-arrival automations.")
    #self.log("old value: " + old)
    if old == "Out":
      self.log("Pre-arrival selected, from 'Out'")
      # Tasks here.
    elif old == "Away":
      self.log("Pre-arrival selected, from 'Away'")
      # Tasks here.

  def execute_just_arrived_automations(self, entity, attribute, old, new, kwargs):
    self.log('Execute Just Arrived automations.')
    self.call_service(globals.max_app, title = "House mode: Just arrived.",\
                                       message = "TTS",\
                                       data = {"media_stream": "alarm_stream",\
                                               "tts_text": "House mode: Just arrived."})
                                               # alarm_stream_max
    day_today = datetime.today().weekday() # Monday is 0 Tue:1 Wed:2 Thu:3 Fri:4 Sat:5 Sun:6
    work_day = self.get_state("binary_sensor.workday_l")

    working_day_return_code, working_day = FunctionLibrary.is_it_a_work_day_today('max')
    self.log(working_day_return_code)
    self.log(working_day)
    #if (working_day_return_code == 1 or working_day_return_code == 2) and self.now_is_between("09:00:00", "22:00:00"):
    if working_day == "off" and self.now_is_between("09:00:00", "22:00:00"):
    #if (work_day == "off" or globals.vacation == "on" or "calendar.england_holidays" == "on") and self.now_is_between("09:00:00", "22:00:00"):
      #self.log("Work_day: " + str(work_day))
      # SB Transporter (Only during the weekend.)
      #self.log("Power on Squeezebox Transporter.")
      SqueezeboxControl.power_on_squeezebox(globals.squeezebox_transporter_power)

      #if GarageLibrary.check_if_garage_closed == "closed":
      #    GarageLibrary.switch_on_garage_door
      garage_door_state = self.get_state(globals.garage_door_entity)
      if garage_door_state == "closed":
        self.call_service("switch/turn_on", entity_id = globals.garage_door_power_switch)
    

  def execute_just_left_automations(self, entity, attribute, old, new, kwargs):
    """This will execute some automations when everybody has left the house."""
    self.log('Execute Just Left automations.')
    #self.call_service(globals.max_app, title = "House mode: Just left.", message = "TTS")
    self.turn_off(globals.garage_light_entity)
    self.call_service("remote/send_command", entity_id = globals.lounge_remote, device="pioneer_amp", command ="power_off")
    garage_door_state = self.get_state(globals.garage_door_entity)
    if garage_door_state == "closed":
      self.call_service("switch/turn_off", entity_id = globals.garage_door_power_switch)
      self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
    else:
      self.call_service(globals.max_app, title = "Garage Alert",
                                         message = "Garage Door is Open.",
                                         data = {"channel":"Garage",
                                                 "tag":globals.garage_door_alert_tag,
                                                 "actions":[globals.android_app_action_close_garage_door]})
    self.call_service("switch/turn_off", entity_id = globals.kettle)
    self.turn_on(globals.person_detection_switch)
    MaxAutomationsLibrary.lock_laptop()
    #SqueezeboxControl.power_off_squeezebox(globals.squeezebox_transporter_power)
    #self.turn_on(entity,brightness=50,color_name="orange")
    self.select_option(globals.lounge_lamps_input_select, globals.dining_lamp)
    # Is it dark?:
    dark_state = self.get_state('binary_sensor.dark')
    if dark_state == "on":
      self.turn_on("scene.exit_stage_left")
    lights_to_fade_down = [globals.landing_light, globals.porch_light]
    for light_to_fade_down in lights_to_fade_down:
      self.log(light_to_fade_down)
      light_state = self.get_state(light_to_fade_down)
      if dark_state == "on" and light_state == "on":
        self.turn_on(light_to_fade_down, brightness = 30, transition = 30)

  def on_house_mode_change(self, entity, attribute, old, new, kwargs):
    self.log("House Mode Changed")
    self.log(new)
    if new == "Away":
      self.log ("Away selected.")
    elif new == "Out":
      self.log("Out selected.")
    elif new == "Home":
      self.log("Home selected.")

#   def power_on_aiwa_hifi(self):
#     self.turn_on(globals.power_aiwa)

#   def power_off_aiwa_hifi(self):
#     self.turn_off(globals.power_aiwa)

###############################################################################################################
# Other functions:
###############################################################################################################

def pre_exit_automation(self):
  self.log("Pre-exit")
  
def away_automations(self):
  self.log("Away automations.")

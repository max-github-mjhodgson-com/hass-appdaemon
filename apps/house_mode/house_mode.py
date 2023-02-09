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

    #FunctionLibrary.i_am_alive()
    #return_code, work_day = FunctionLibrary.is_it_a_work_day_today("max")
    #self.log(str(return_code) + str(work_day))
    #self.log(globals.remote_control['pioneer_amp']['power_off'])

    # States:
    self.listen_state(self.on_everyone_is_out, "group.persons", new="not_home", duration = 20)
    self.listen_state(self.on_someone_just_arrived_home, "group.persons", new="home", duration = 30)
    self.listen_state(self.on_house_mode_just_left_timeout, globals.house_mode_selector, new="Just Left", duration = 30)
    self.listen_state(self.on_house_mode_just_arrived_timeout, globals.house_mode_selector, new="Just Arrived", duration = 30)
    self.listen_state(self.on_execute_just_arrived_automations, globals.house_mode_selector, new="Just Arrived", old = "Out", duration = 10)
    self.listen_state(self.on_execute_just_left_automations, globals.house_mode_selector, new = "Just Left", old = "Home", duration = 10)
    self.listen_state(self.on_execute_pre_arrival_automations, globals.house_mode_selector, new = "Pre-Arrival", duration = 10)
    self.listen_state(self.on_house_mode_pre_departure_selected, globals.house_mode_selector, new = "Pre-Departure", duration = 10)
    self.listen_state(self.on_house_mode_change, globals.house_mode_selector)

    # Events:
    self.listen_event(self.on_pre_departure_event, "pre_departure_activated")
    self.listen_state(self.on_button_press_pre_departure, 'input_button.pre_departure')
###############################################################################################################
# Callback functions:
############################################################################################################### 
  def on_everyone_is_out(self, entity, attribute, old, new, kwargs):
    self.log('The last person just left the house.')
    self.select_option(globals.house_mode_selector, "Just Left")

  def on_someone_just_arrived_home(self, entity, attribute, old, new, kwargs):
    self.log('Someone just arrived home.: ' + entity)
    self.log(attribute)
    self.select_option(globals.house_mode_selector, "Just Arrived")
    # Run any specific person automations.
    # Find out who by iterating the persons group and getting the state of each memmber.
    persons_at_home = self.get_state("group.persons", attribute = "entity")

  def on_house_mode_just_left_timeout(self, entity, attribute, old, new, kwargs):
    self.log('House Mode Just Left has timed out, switching to Out.')
    self.select_option(globals.house_mode_selector, "Out")
    
  def on_house_mode_just_arrived_timeout(self, entity, attribute, old, new, kwargs):
    self.log('House Mode Just Arrived has timed out, switching to Home.')
    self.select_option(globals.house_mode_selector, "Home")
  
  # Manuallly triggered pre-arrival.
  def on_execute_pre_arrival_automations(self, entity, attribute, old, new, kwargs):
    self.log("Pre-arrival automations.")
    #self.log("old value: " + old)
    if old == "Out":
      self.log("Pre-arrival selected, from 'Out'")
      # Tasks here.
    elif old == "Away":
      self.log("Pre-arrival selected, from 'Away'")
      # Tasks here.

  def on_execute_just_arrived_automations(self, entity, attribute, old, new, kwargs):
    self.log('Execute Just Arrived automations.')
    self.call_service(globals.max_app, title = "House mode: Just arrived.",\
                                       message = "TTS",\
                                       data = {"media_stream": "alarm_stream",\
                                               "tts_text": "House mode: Just arrived."})
                                               # alarm_stream_max
    #day_today = datetime.today().weekday() # Monday is 0 Tue:1 Wed:2 Thu:3 Fri:4 Sat:5 Sun:6

    working_day_return_code, working_day = FunctionLibrary.is_it_a_work_day_today('max') # To do: Derive users from who has arrived.
    self.log(working_day_return_code)
    self.log(working_day)
    if working_day == "off" and self.now_is_between("09:00:00", "22:00:00"):
      SqueezeboxControl.power_on_squeezebox(globals.squeezebox_transporter_power)
      garage_door_state = GarageLibrary.check_if_garage_closed()
      if garage_door_state == "closed":
        GarageLibrary.switch_on_garage_door()

  def on_execute_just_left_automations(self, entity, attribute, old, new, kwargs):
    """This will execute some automations when everybody has left the house."""
    if old != "unavailable" and (old == "Home" or old == "Pre-Departure"):
      self.just_left_automations()
   

  def on_house_mode_change(self, entity, attribute, old, new, kwargs):
    base_message = "House Mode Changed: "
    if new == "Away":
      self.log (base_message + "Away selected.")
    elif new == "Out":
      self.log(base_message + "Out selected.")
    elif new == "Home":
      self.log(base_message + "Home selected.")
    elif new == "Sleep":
      self.log(base_message + "Sleep selected.")

  def on_house_mode_pre_departure_selected(self, entity, attribute, old, new, kwargs):
    self.log("Pre-departure selected")
    if old != "Home": # Can only set this if currently at home.
      self.select_option(globals.house_mode_selector, old)
    else:
      self.log("Pre-departure from home.")
      self.pre_departure_automations()

  # Listen for an external event.
  def on_pre_departure_event(self, event, data, kwargs):
    self.log("Event recieved.")

  def on_button_press_pre_departure(self, entity, attribute, old, new, kwargs):
    self.log("Departure Button Pressed.")
    self.select_option(globals.house_mode_selector, "Pre-departure")

###############################################################################################################
# Other functions:
###############################################################################################################

  def pre_departure_automations(self):
    self.log("Pre-departure automations")
    dark_state = self.get_state(globals.dark_sensor)
    if dark_state == "on":
      self.log("It is dark.")
      # Run a scene.
      self.turn_on("scene.exit_stage_left")
    current_season = self.get_state("sensor.meteorological_season")
    if current_season == "winter":
      self.call_service(globals.max_app, title = "Check heating.",\
                                         message = "TTS",\
                                         data = {"media_stream": "alarm_stream",\
                                                 "tts_text": "Remember to check the heating."})

  def just_left_automations(self):
    self.log("Execute just left automations.")
    #self.call_service(globals.max_app, title = "House mode: Just left.", message = "TTS")
    self.call_service("remote/send_command", entity_id = globals.lounge_remote, device="pioneer_amp", command ="power_off")
    self.turn_off(globals.garage_light_entity)
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

    self.select_option(globals.lounge_lamps_input_select, globals.dining_lamp)
    # Is it dark?:
    dark_state = self.get_state(globals.dark_sensor)
    if dark_state == "on":
      self.turn_on("scene.exit_stage_left")
    #lights_to_fade_down = [globals.landing_light, globals.porch_light]
    #for light_to_fade_down in lights_to_fade_down:
    #  self.log(light_to_fade_down)
    #  light_state = self.get_state(light_to_fade_down)
    #  if dark_state == "on" and light_state == "on":
    #    self.turn_on(light_to_fade_down, brightness = 30, transition = 30)
    #self.turn_off(globals.dining_table_light)




  def away_automations(self):
    self.log("Away automations.")

#   def power_on_aiwa_hifi(self):
#     self.turn_on(globals.power_aiwa)

#   def power_off_aiwa_hifi(self):
#     self.turn_off(globals.power_aiwa)


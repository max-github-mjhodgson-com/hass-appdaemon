# House Mode App.
#
# Max Hodgson 2023
# Version: 10052023.01
#
# Controls the mode that the house is in.
# 
# Needs an input_select configured in Home Assistant.
#

import appdaemon.plugins.hass.hassapi as hass

import datetime
import time
import os

import globals_module as globals

from datetime import datetime

class House_Mode(hass.Hass):

  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)

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

    #self.change_house_mode(house_mode = "home")
    

    current_house_mode = self.get_state(globals.house_mode_selector)
    self.log("Current house mode: " + str(current_house_mode))
    if current_house_mode == "Just Arrived":
      self.log("Changing house mode to home.")
      self.select_option(globals.house_mode_selector, "Home")
    elif current_house_mode == "Just Left":
      self.log("Changing house mode to out.")
      self.select_option(globals.house_mode_selector, "Out")

    global people_at_home
    people_at_home = []
    self.get_people_at_home()
    self.log("People at home: " + str(people_at_home))
    if people_at_home == []:
      self.log("Nobody is at home.")
      self.select_option(globals.house_mode_selector, "Out")
    else:
      self.log("Someone is at home.")
      self.select_option(globals.house_mode_selector, "Home")
    #  self.log("Max is at home.")
    #  MaxAutomationsLibrary.run_arrival_automations_for_max()

    #self.log(self.entities.group.persons.attributes.entity_id)

    #return_code, work_day = FunctionLibrary.is_it_a_work_day_today("max")
    #self.log(str(return_code) + str(work_day))
    #self.log(globals.remote_control['pioneer_amp']['power_off'])

    # States:
    self.group_persons_entity = self.get_entity("group.persons")
    self.group_persons_entity.listen_state(self.on_everyone_is_out, new = "not_home", duration = 20)
    self.group_persons_entity.listen_state(self.on_someone_just_arrived_home, new = "home", duration = 20)
    self.house_mode_selector_entity = self.get_entity(globals.house_mode_selector)
    self.house_mode_selector_entity.listen_state(self.on_house_mode_just_left_timeout, new = "Just Left", old = "Home", duration = 30)
    self.house_mode_selector_entity.listen_state(self.on_house_mode_just_arrived_timeout, new = "Just Arrived", old = ["Out", "Away"], duration = 30)
    self.house_mode_selector_entity.listen_state(self.on_execute_just_arrived_automations, new = "Just Arrived", old = "Out", duration = 10)
    self.house_mode_selector_entity.listen_state(self.on_execute_just_left_automations, new = "Just Left", old = "Home", duration = 10)
    self.house_mode_selector_entity.listen_state(self.on_execute_pre_arrival_automations, new = "Pre-Arrival", old = lambda x : x not in ["unknown", "unavailable"], duration = 10)
    self.house_mode_selector_entity.listen_state(self.on_house_mode_pre_departure_selected, new = "Pre-Departure", old = lambda x : x not in ["unknown", "unavailable"], duration = 10)
    self.house_mode_selector_entity.listen_state(self.on_house_mode_change)
    people = self.get_state("group.persons", attribute = "entity_id")
    list_of_people = []
    for person in people:
      self.log(person)
      list_of_people.append(person)
      self.person_entity = self.get_entity(person)
      self.person_entity.listen_state(self.on_who_has_left_or_entered, duration = 10)
    #self.log(list_of_people)
    #self.listen_state(self.on_who_has_left_or_entered, list_of_people, duration = 10)

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
    self.get_people_at_home()
    self.log("People at home: " + str(people_at_home))
    if globals.person_max in people_at_home:
      self.log("Max is at home, run auytomations.")
      MaxAutomationsLibrary.run_arrival_automations_for_max()
      self.log("Post Max automations run.")
    self.run_in(self.change_house_mode, 10, house_mode = "Home")

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
    self.log('Execute just arrived global automations.')
    self.call_service(globals.max_app, title = "House mode: Just arrived.",\
                                       message = "TTS",\
                                       data = {"media_stream": "alarm_stream",\
                                               "tts_text": "House mode: Just arrived."})
                                               # alarm_stream_max
    #day_today = datetime.today().weekday() # Monday is 0 Tue:1 Wed:2 Thu:3 Fri:4 Sat:5 Sun:6
    self.run_in(self.change_house_mode, 10, house_mode = "Home")
  
  def on_execute_just_left_automations(self, entity, attribute, old, new, kwargs):
    """This will execute automations when everybody has left the house."""
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
    self.log("Event received.")

  def on_button_press_pre_departure(self, entity, attribute, old, new, kwargs):
    self.log("Departure Button Pressed.")
    self.select_option(globals.house_mode_selector, "Pre-departure")

  def on_who_has_left_or_entered(self, entity, attribute, old, new, kwargs):
    if old == "home":
      self.log(str(entity) + " has left.")
    if new == "home":
      self.log(str(entity) + " has entered.")


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

  def away_automations(self):
    self.log("Away automations.")

#   def power_on_aiwa_hifi(self):
#     self.turn_on(globals.power_aiwa)

#   def power_off_aiwa_hifi(self):
#     self.turn_off(globals.power_aiwa)

  def get_people_at_home(self):
    persons_at_home = self.get_state("group.persons", attribute = "entity_id")
    #self.log("Persons at home: " + str(persons_at_home))
    for person_at_home in persons_at_home:
      #self.log(person_at_home)
      home_status = self.get_state(person_at_home)
      #self.log("Home status: " + home_status)
      if home_status == "home":
        #self.log("Person element: " + person_at_home)
        people_at_home.append(person_at_home)
    #self.log("People at home: " + str(people_at_home))
    return people_at_home

  def change_house_mode(self, cb_args):
    house_mode_to_change_to = cb_args["house_mode"]
    self.log("House mode change: " + str(house_mode_to_change_to))
    self.select_option(globals.house_mode_selector, house_mode_to_change_to)

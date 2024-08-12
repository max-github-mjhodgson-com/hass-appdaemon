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

    # Load external app libraries:
    self.function_library = self.get_app("function_library")
    self.garage_library = self.get_app("garage")
    self.squeezebox_control_library = self.get_app("squeezebox_control")
    self.max_automations_library = self.get_app("max_automations")

    # Setup some variables:
    self.unavailable_states = ["unknown", "unavailable"]

    
    # State Monitors:
    self.listen_state(self.on_everyone_is_out, entity_id = "group.persons", new = "not_home", duration = 20, immediate = True)
    self.listen_state(self.on_someone_just_arrived_home, entity_id = "group.persons", new = "home", duration = 20, immediate = True)
    self.house_mode_selector_entity = self.get_entity(globals.house_mode_selector)
    self.listen_state(self.on_execute_just_left_automations, entity_id = globals.house_mode_selector, new = "Just Left", old = "Home", duration = 10, immediate = True)
    self.listen_state(self.on_execute_just_arrived_automations, entity_id = globals.house_mode_selector, new = "Just Arrived", old = ["Out", "Away"], duration = 10, immediate = True)
    self.listen_state(self.on_house_mode_out_timeout, entity_id = globals.house_mode_selector, new = "Out", old = "Home", duration = 259200, immediate = True) # 259200 = 3 days
    self.listen_state(self.on_house_mode_change, entity_id = globals.house_mode_selector, duration = 2, immediate = True)
    self.house_mode_selector_entity.listen_state(self.on_execute_pre_arrival_automations, new = "Pre-Arrival", duration = 10) # old = lambda x : x not in ["unknown", "unavailable"], duration = 10)
    self.house_mode_selector_entity.listen_state(self.on_house_mode_pre_departure_selected, new = "Pre-Departure", duration = 10) #, old = lambda x : x not in ["unknown", "unavailable"], duration = 10)
    
    people = self.get_state("group.persons", attribute = "entity_id")
    self.log(people)
    self.listen_state(self.on_who_has_left_or_entered, entity_id = people, duration = 10)

    # Event Monitors:
    self.listen_event(self.on_pre_departure_event, "pre_departure_activated")
    self.listen_state(self.on_button_press_pre_departure, 'input_button.pre_departure')

###############################################################################################################
# Callback functions:
############################################################################################################### 
  def on_everyone_is_out(self, entity, attribute, old, new, cb_args):
    if old not in self.unavailable_states:
      if self.get_state(globals.house_mode_selector) == "Home":
        self.log('The last person just left the house.')
        self.select_option(globals.house_mode_selector, "Just Left")

  def on_someone_just_arrived_home(self, entity, attribute, old, new, cb_args):
    self.log("Someone just arrived home.")
    any_movement = self.get_state(globals.house_movement_sensors)
    if any_movement != "off":
      self.log("Someone moved.")
    self.select_option(globals.house_mode_selector, "Just Arrived")
    
    # Run any specific person automations.
    self.get_people_at_home()
    self.log("People at home: " + str(self.people_at_home))
    if globals.person_max in self.people_at_home:
      self.log("Max is at home, run automations.")
      self.max_automations_library.run_arrival_automations_for_max()
      self.log("Post Max automations run.")
    self.run_in(self.on_change_house_mode_cb, 10, house_mode = "Home")

  def on_house_mode_just_left_timeout(self, entity, attribute, old, new, cb_args):
    self.log('House Mode Just Left has timed out, switching to Out.')
    self.select_option(globals.house_mode_selector, "Out")
    
  def on_house_mode_just_arrived_timeout(self, entity, attribute, old, new, cb_args):
    self.log('House Mode Just Arrived has timed out, switching to Home.')
    if old != "Out":
      self.select_option(globals.house_mode_selector, "Home")
  
  # Manuallly triggered pre-arrival. Todo: Run automations when a zone is entered.
  def on_execute_pre_arrival_automations(self, entity, attribute, old, new, cb_args):
    if old not in self.unavailable_states:
      self.log("Pre-arrival automations.")
      #self.log("old value: " + old)
    if old == "Out":
      self.log("Pre-arrival selected, from 'Out'")
      # Tasks here.
    elif old == "Away":
      self.log("Pre-arrival selected, from 'Away'")
      # Tasks here.

  def on_execute_just_arrived_automations(self, entity, attribute, old, new, cb_args):
    self.log('Execute just arrived global automations.')
    if old != "unavailable":
      self.run_in(self.on_change_house_mode_cb, 20, house_mode = "Home")
      self.call_service(globals.max_app, title = "House mode: Just arrived.",\
                                         message = "TTS",\
                                         data = {"media_stream": "alarm_stream",\
                                                 "tts_text": "House mode: Just arrived."})
                                                 # alarm_stream_max
 
  def on_execute_just_left_automations(self, entity, attribute, old, new, cb_args):
    """This will execute automations when everybody has left the house."""
    if old != "unavailable" and (old == "Home" or old == "Pre-Departure"):
      self.log("Just left activated.")
      self.run_in(self.on_change_house_mode_cb, 20, house_mode = "Out")
      self.just_left_automations()

  def on_house_mode_change(self, entity, attribute, old, new, cb_args):
    if new not in self.unavailable_states and old not in self.unavailable_states:
      current_house_mode = self.get_state(globals.house_mode_selector)
      self.log("Current house mode: " + str(current_house_mode))
      base_message = "House Mode Changed: "
      match new:
        case "Away":
          if old == "Out":
            self.log(base_message + "Away selected.")
        case "Out":
          self.log(base_message + "Out selected.")
        case "Home":
          self.log(base_message + "Home selected. old: " + str(old))
          self.log(self.get_people_at_home())
        case "Sleep":
          if old == "Home":
            self.log(base_message + "Sleep selected.")
            self.log(self.get_people_at_home())

  def on_house_mode_pre_departure_selected(self, entity, attribute, old, new, cb_args):
    if old not in self.unavailable_states:
      self.log("Pre-departure selected")
      if old != "Home": # Can only set this if currently at home.
        self.select_option(globals.house_mode_selector, old)
      else:
        self.log("Pre-departure from home.")
        self.pre_departure_automations()

  # Listen for an external event.
  def on_pre_departure_event(self, event, data, cb_args):
    self.log("Event received.")

  def on_button_press_pre_departure(self, entity, attribute, old, new, cb_args):
    self.log("Departure Button Pressed.")
    self.select_option(globals.house_mode_selector, "Pre-departure")

  def on_who_has_left_or_entered(self, entity, attribute, old, new, cb_args):
    #person_and_name = entity.split(".")
    #name_only = person_and_name[1]
    #workday_person = self.function_library.is_it_a_work_day_today(name_only)
    friendly_name = self.get_state(entity, attribute = "friendly_name")
    if old == "home":
      self.log(str(friendly_name) + " has left.")
    if new == "home":
      self.log(str(friendly_name) + " has entered.")

  def on_change_house_mode_cb(self, cb_args):
    house_mode_to_change_to = cb_args["house_mode"]
    self.log("House mode change: " + str(house_mode_to_change_to))
    self.select_option(globals.house_mode_selector, house_mode_to_change_to)

  # This will change the house to "away" mode after it has been set to "out" mode for a period of time.
  def on_house_mode_out_timeout(self, entity, attribute, old, new, cb_args):
    self.log("Changing to Away mode.")
    self.select_option(globals.house_mode_selector, "Away")
    

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
    self.call_service("remote/send_command", entity_id = globals.lounge_remote, device = "pioneer_amp", command ="power_off")
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
    devices_off_on_exit = [globals.kettle, globals.tv_power, globals.lounge_fan]
    for device in devices_off_on_exit:
      self.log("Turning off: " + str(device))
      self.call_service("switch/turn_off", entity_id = device)
    self.turn_on(globals.person_detection_switch)
    self.max_automations_library.lock_laptop()

    # Turn off Transporter and reset power flag:
    self.squeezebox_control_library.power_off_squeezebox(globals.squeezebox_transporter_power)
    self.set_state(globals.tranporter_session_power_flag, state = "off", attributes = {"friendly_name": globals.tranporter_session_power_flag_name})

    self.log("Change lamps input select stage 1.")
    #self.select_option(globals.lounge_lamps_input_select, globals.dining_lamp)
    self.log("Change lamps input select stage 2.")
    # Is it dark?:
    dark_state = self.get_state(globals.dark_sensor)
    if dark_state == "on":
      self.turn_on("scene.exit_stage_left")
    self.log("Change lamps input select stage 3.")

  def away_automations(self):
    self.log("Away automations.")
    # e.g. 
    # Put heating into defrost mode and switch off hot water.
    # Stop media servers from auto-powering on.
    # Stop blinds and curtains from auto opening.
    # Put lights into random mode.

  def get_people_at_home(self):
    self.people_at_home = []
    persons_at_home = self.get_state("group.persons", attribute = "entity_id")
    if persons_at_home != "":
      #self.log("Persons in home group home: " + str(persons_at_home))
      for person_at_home in persons_at_home:
        #self.log(person_at_home)
        home_status = self.get_state(person_at_home)
        #self.log("Home status: " + home_status)
        if home_status == "home":
          #self.log("Person element: " + person_at_home)
          self.people_at_home.append(person_at_home)
      #self.log("People who are at home: " + str(self.people_at_home))
    else:
      self.log("No data.")
      self.people_at_home = ""
    return self.people_at_home


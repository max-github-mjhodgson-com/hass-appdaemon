# Responds to Calendar Events.
#
# Max Hodgson 2023
# Version: 14022023.01
#
# This can check whether specific named event is in progress.
# This can also perform tasks based on calendar event.
# Calendar events to perform tasks:
#   garage door <open|close>
#   garage power <on|off>
#   house mode <out|away|pre-arrival>
#   telegram message <message>
# 

import appdaemon.plugins.hass.hassapi as hass

import os

import globals_module as globals

from datetime import datetime

class Calendar_Automations(hass.Hass):

  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    # Load external app libraries:
    #self.function_library = self.get_app("function_library")  # Not currently used.
    self.garage_library = self.get_app("garage")
    self.house_mode_library = self.get_app("house_mode")
    self.squeezebox_library = self.get_app("squeezebox_control")
    self.door_phone_library = self.get_app("doorphone")
    self.car_library = self.get_app("car")
    
    # Listen for events:
    self.listen_event(self.on_calendar_event, entity_id = globals.house_calendar)

    # Test event check.
    #self.log("Event test.")
    #fred = self.calendar_check_if_event_is_in_progress(globals.house_calendar, "Test Event 13")
    #self.log("Event: " + str(fred))

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################
  def on_calendar_event(self, event_name, data, kwargs):
     if event_name == "state_changed":
       entity_id = data.get("entity_id")
       if entity_id == globals.house_calendar:
         old_state = data.get("old_state")
         old_event_state = old_state.get("state")
         new_state = data.get("new_state")
         new_event_state = new_state.get("state")
         #self.log(new_event_state + ":" + old_event_state)
       #  Event started. (Returns: calendar_title)
       if old_event_state == "off" and new_event_state == "on":
         attributes = data.get("new_state", {}).get("attributes")
         if attributes != None:
           calendar_title = attributes.get("message")
           # Run event start actions.
           self.calendar_event_start(calendar_title)
       # Event ended. (Returns: calendar_title)
       elif old_event_state == "on" and new_event_state == "off":
         attributes = data.get("old_state", {}).get("attributes")
         if attributes != None:
           calendar_title = attributes.get("message")
           # Run event end actions.
           self.calendar_event_end(calendar_title)
       # Calendar event updated (through the UI). (Returns: calendar_title)
       elif old_event_state == "off" and new_event_state == "off":
         attributes = data.get("new_state", {}).get("attributes")
         if attributes != None:
           calendar_title = attributes.get("message")

###############################################################################################################
# Other functions:
###############################################################################################################
  def calendar_event_start(self, calendar_event_title):
      self.log("Calendar event started: " + calendar_event_title)
      calendar_event_title_split = calendar_event_title.split().lower()
      self.log("Calendar title: " + str(calendar_event_title_split))
      calendar_event_title_word_count = len(calendar_event_title_split)
      if calendar_event_title_word_count > 1:
        command_string = ' '.join(calendar_event_title_split[0:2])
        match command_string:
          case "garage door":
            if calendar_event_title_split[2] == "open":
              self.log("Garage door open.")
              self.garage_library.power_on_and_open_garage
            elif calendar_event_title_split[2] == "close":
              self.log("Garage door close.")
              self.garage_library.close_garage_and_power_off
          case "garage power":
            if calendar_event_title_split[2] =="on":
              self.log("Garage power on.")
              self.garage_library.switch_on_garage_door
            elif calendar_event_title_split[2] =="off":
              self.log("Garage power off.")
              self.garage_library.switch_off_garage_door
          case "telegram message":
            telegram_message = calendar_event_title_split[2:]
            self.log("Telegram message: " + " ".join(telegram_message))
            self.call_service(globals.max_telegram, title = "Calendar Reminder: ", message = " ".join(telegram_message))
          case "ha message":
            ha_message = calendar_event_title_split[2:]
            self.log("HA message: " + " ".join(ha_message))
            self.call_service(globals.max_app, title = "Calendar Reminder: ", message = " ".join(ha_message))
          case "house mode" :
            self.log("House Mode.")
            available_house_modes = ["out", "away", "pre-arrival"]
            house_mode = calendar_event_title_split[2]
            if house_mode in available_house_modes:
              self.select_option(globals.house_mode_selector, house_mode)


  def calendar_event_end(self, calendar_event_title):
      self.log("Calendar event ended: " + calendar_event_title)
      calendar_event_title_split = calendar_event_title.split()
      calendar_event_title_word_count = len(calendar_event_title_split)
      if calendar_event_title_split[0].lower() == "garage":
        if calendar_event_title_split[1].lower() =="door":
          self.log("Garage close.")
          self.garage_library.close_garage_and_power_off
        elif calendar_event_title_split[1].lower() =="power" and calendar_event_title_split[2].lower() =="on":
           self.log("Garage power off.")
           self.garage_library.switch_off_garage_door

  # Check if event is in progress.
  # Usage:
  #   self.log(self.calendar_check_if_event_is_in_progress(globals.house_calendar, "Test Event 13"))
  # Returns "on" or "off"
  def calendar_check_if_event_is_in_progress(self, calendar_name, calendar_event_title):
    return_code = "off"
    calendar_status = self.get_state(calendar_name)
    if calendar_status == "on":
      event_in_progress = self.get_state(calendar_name, attribute = "message")
      if event_in_progress.lower() == calendar_event_title.lower():
        return_code = "on"
    return return_code

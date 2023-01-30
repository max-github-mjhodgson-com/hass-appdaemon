# Responds to Calendar Events.
#
# Max Hodgson 2023

import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime
import globals

class Calendar(hass.Hass):

  def initialize(self):
    self.log("=" * 30)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    # Load external apps:
    global FunctionLibrary
    FunctionLibrary = self.get_app("function_library")
        
    global GarageLibrary
    GarageLibrary = self.get_app("garage")

    global HouseModeLibrary
    HouseModeLibrary = self.get_app("house_mode")
        
    global SqueezeboxLibrary
    SqueezeboxLibrary = self.get_app("squeezebox_control")

    global DoorPhoneLibrary
    DoorPhoneLibrary = self.get_app("doorphone")

    global CarLibrary
    CarLibrary = self.get_app("car")

    
    # Listen for events:
    self.listen_event(self.on_calendar_event, entity_id = globals.house_calendar)


    # Test event check.
    ##self.log(self.calendar_check_if_event_is_in_progress(globals.house_calendar, "Test Event 13"))


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
      calendar_event_title_split = calendar_event_title.split()
      calendar_event_title_word_count = len(calendar_event_title_split)
      if calendar_event_title_split[0].lower() == "garage":
        if calendar_event_title_split[1].lower() =="door":
          self.log("Garage open.")
          GarageLibrary.power_on_and_open_garage
        elif calendar_event_title_split[1].lower() =="power" and calendar_event_title_split[2].lower() =="on":
           self.log("Garage power on.")
           GarageLibrary.switch_on_garage_door
        elif calendar_event_title_split[1].lower() =="power" and calendar_event_title_split[2].lower() =="off":
          self.log("Garage power off.")
          GarageLibrary.switch_off_garage_door
      elif calendar_event_title_split[0].lower() == "telegram" and calendar_event_title_split[1].lower() == "message":
        telegram_message = calendar_event_title_split[2:]
        self.log("Telegram message: " + " ".join(telegram_message))
        self.call_service(globals.max_telegram, title = "Calendar Reminder", message = " ".join(telegram_message))
      elif calendar_event_title_split[0].lower() == "ha" and calendar_event_title_split[1].lower() == "message":
        ha_message = calendar_event_title_split[2:]
        self.log("HA message: " + " ".join(ha_message))
        self.call_service(globals.max_app, title = "Calendar Reminder", message = " ".join(ha_message))
      elif calendar_event_title_split[0:1].lower() == "house mode":
        self.log("House Mode.")
        available_house_modes = ["Out", "Away", "Pre-arrival"]
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
          GarageLibrary.close_garage_and_power_off
        elif calendar_event_title_split[1].lower() =="power" and calendar_event_title_split[2].lower() =="on":
           self.log("Garage power off.")
           GarageLibrary.switch_off_garage_door

  # Check if event is in progress.
  # Usage:
  #   self.log(self.calendar_check_if_event_is_in_progress(globals.house_calendar, "Test Event 13"))
  # Returns "yes" or "no"
  def calendar_check_if_event_is_in_progress(self, calendar_name, calendar_event_title):
    event_in_progress = self.get_state(calendar_name, attribute = "message")
    if event_in_progress.lower() == calendar_event_title.lower():
      return "on"
    else:
      return "off"

# Doorphone App
#
# Max Hodgson 2023
# Version: 10052023.01
#
# Doorphone automations for Grandstream SIP doorphone.
#
# Uses websocket triggers configured in Home Assistant.
# Also uses Frigate for the CCTV.
#

import appdaemon.plugins.hass.hassapi as hass
import os
#import requests
import time

import globals_module as globals

from datetime import timedelta
from datetime import datetime


class Doorphone(hass.Hass):

  # Monitors:
  # Doorphone events for:
  # 600 - Card used.
  # 500 - Doorbell
  # 501 - Doorbell (Call in).
  # 504 - Doorbell.
  # 900 - Motion detected.
  # 1100 - Tamper
  # 1101 - System up.
  # 1102 - System Reboot.
  
  # Doorphone for Card number.
  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    self.camera_location = "front_doorbell"
    # Uses http as it is on the internal network.
    #self.camera_image_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/"+ self.camera_location +"/latest.jpg"
    self.media_cctv_path = "/config/media/cctv/"
    self.camera_image_path = self.media_cctv_path + self.camera_location + "/tmp/"
    self.latest_camera_image = self.media_cctv_path + self.camera_location + "/latest/person.jpg"
    #self.camera_image_name = self.camera_image_path + self.camera_location + "_latest.jpg"

    # Load external app libraries:
    #self.function_library = self.get_app("function_library")  # Not currently used.
    self.mqtt = self.get_plugin_api("MQTT")
    self.garage_library = self.get_app("garage")
    self.cctv_library = self.get_app("cctv")
    self.asterisk_comms = self.get_app("asterisk_comms")  # Example: self.asterisk_comms.hangup(globals.doorphone_extension_number)
    
    # Last doorbell ring time setup:
    self.last_ring = datetime.now() - timedelta(seconds = 35)

    self.doorphone_event_type = "sensor.doorphone_event_type"
    #self.doorphone_event_type_entity = self.get_entity(self.doorphone_event_type)
    self.doorphone_message_title = "Door Phone Alert"

    #snapshot_filename, latest_picture_filename = self.cctv_library.get_picture_from_frigate("front_doorbell", "person")
    #self.log("Snapshot filename: " + str(snapshot_filename))
    #self.call_service("telegram_bot/send_photo", file = self.latest_camera_image, caption = "Person at front.(Doorphone)")    


    # Testing:
    #self.take_picture(camera_location = self.camera_location, picture_type = "doorbell", picture_caption = "Doorbell Button Pressed (API).")
    #self.take_picture("front_doorbell", "doorphone", "test")
    #self.cctv_library.take_picture(self.camera_location = "front_doorbell", picture_type = "doorbell", picture_caption = "Test.")
    #self.run_in(self.cctv_library.get_latest_camera_picture, 1, image_url = self.camera_image_url, image_filename = "/config/tmp/test.jpg")
    #self.cctv_library.get_latest_camera_picture( image_url = self.camera_image_url, image_filename = "/config/tmp/test.jpg")
    #self.run_in(self.cctv_library.get_latest_camera_picture, 10, image_url = self.camera_image_url, image_filename = "/config/media/cctv/fred.jpg")
    
    #self.take_reboot_picture("Message", "/config/media/cctv/fred.jpg", self.camera_image_url)

    # State monitors
    self.new_event_handler1 = self.listen_state(self.on_event_detected, self.doorphone_event_type, old = "0", new = "900")
    self.new_event_handler2 = self.listen_state(self.on_event_detected, self.doorphone_event_type, old = "0", new = "1102")
    self.card_used_handler = self.listen_state(self.on_doorphone_card_used, self.doorphone_event_type, new = "600")
    self.system_up_handler = self.listen_state(self.on_doorphone_system_up, self.doorphone_event_type, new = "1101")
    
    self.doorbell_button_handler = self.listen_state(self.on_doorphone_doorbell_button_pressed, self.doorphone_event_type, new = "500")
    self.doorbell_button_handler = self.listen_state(self.on_doorphone_doorbell_button_pressed, self.doorphone_event_type, new = "501")
    self.doorbell_button_handler = self.listen_state(self.on_doorphone_doorbell_button_pressed, self.doorphone_event_type, new = "502")
    self.doorbell_button_handler = self.listen_state(self.on_doorphone_doorbell_button_pressed, self.doorphone_event_type, new = "504")

    self.doorbell_tamper_handler = self.listen_state(self.on_doorphone_tamper, self.doorphone_event_type, new = "1100")
    self.person_at_front_frigate = self.listen_state(self.on_person_at_front_new, globals.front_doorbell_person_sensor, new = "on")
    self.doorphone_poe_power_handler = self.listen_state(self.on_doorphone_power_off, globals.doorphone_power_poe_injector, new = "off", duration = 10)
    self.doorphone_ping_sensor_handler = self.listen_state(self.on_doorphone_dropped_off_network, globals.doorphone_ping, new = "off", duration = 10)
    
    # Event monitors:
    self.motion_timer_finished_handler = self.listen_event(self.on_motion_undetected, "timer.finished", entity_id = globals.frontdoor_motion_timer)
    # Test: self.listen_for_reset_doorbell_pressed = self.listen_event(self.reset_doorbell_pressed_flag, "reset_doorbell_pressed_flag", oneshot=True)
    # Test: self.porch_light_timer_finished_handler = self.listen_event(self.on_porch_light_timer_finished, "timer.finished", entity_id = globals.porch_light_timer, oneshot=True, old_brightness = 30)

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################
  def on_event_detected(self, entity, attribute, old, new, kwargs):
    #self.log("Event detected: " + new)
    if new == "900":
      self.motion_detected()
    elif new == "1102":
      self.system_rebooted()
  
  # Motion undetected via timer timeout.
  def on_motion_undetected(self, event, data, kwargs):
    #self.log("Motion Un-detected.")
    motion_detected = "0"

  # RFID Card Used.
  def on_doorphone_card_used(self, entity, attribute, old, new, kwargs):
    self.log("doorphone-card-used.py: Card Used.")
    card_number = self.get_state("sensor.doorphone_card_number")
    #self.log(card_number)
    #self.call_service("python_script/set_state", entity_id = self.doorphone_event_type, state = "0") ## Retired.
    self.set_state(self.doorphone_event_type, state='0')
    #self.call_service("python_script/set_state", entity_id = "sensor.doorphone_card_number", state = "0")
    self.set_state("sensor.doorphone_card_number", state='0')
    self.log("Card used: %s", card_number)
    self.call_service(globals.notify_max_all, title = self.doorphone_message_title, message = "Card used.")
    caption_text = "Doorbell Card Used: "+card_number
    self.take_picture(camera_location = self.camera_location, picture_type="card", picture_caption = caption_text)
    
    if card_number in globals.cards_garage_door:
      self.log("Card number found in Garage Door List.")
      self.call_service(globals.notify_max_all, title = self.doorphone_message_title, message = "Card used: Garage Door Open.")
      door_state = self.get_state(globals.garage_door_entity)
      self.log(door_state)
      if door_state == "closed":
        self.log("Garage is closed, opening.")
        self.garage_library.power_on_and_open_garage()
      else:
        self.log("Garage is open, closing.")
        self.garage_library.close_garage_and_power_off()

  # Doorbell button has been pressed.
  def on_doorphone_doorbell_button_pressed(self, entity, attribute, old, new, kwargs):
    if old not in ["unknown", "unavailable"]:
      self.log("Doorbell pressed.")
      self.log("New: " + new)
      if self.get_state(globals.porch_light_timer) != "active":  # If we're already in an active period, don't change brightness.
        self.log("Porch light timer is not active.")
        porch_light_brightness = self.get_state(globals.porch_light, attribute="brightness")
      porch_light_on = self.get_state(globals.porch_light)
      if porch_light_on != 'on':
        pass
      elif porch_light_brightness > 0:
        self.log("Porch light is ON and it's brightness is: " + str(porch_light_brightness))
        self.call_service("timer/start", entity_id = globals.porch_light_timer, duration = "600")
        self.porch_light_timer_finished_handler = self.listen_event(self.on_porch_light_timer_finished, "timer.finished", entity_id = globals.porch_light_timer, oneshot=True, old_brightness = porch_light_brightness)
        self.turn_on(globals.porch_light, brightness=255, transition=2)
      if self.last_ring < datetime.now() - timedelta(seconds = 30):
        self.last_ring = datetime.now()
        self.log("Bell push over 30 seconds.")
        if new != 501: # Dial in
          self.call_service(globals.notify_max_all, title = "Door Phone Alert (Button Pushed).",\
                                                    message = "Doorbell Button Pressed (API).",\
                                                    data = {"clickAction":globals.lovelace_cctv_tab,\
                                                            "image":globals.frigate_current_frontdoor_pic_url})
          self.take_picture(camera_location = self.camera_location, picture_type = "doorbell", picture_caption = "Doorbell Button Pressed (API).")
          #self.cctv_library.get_picture_from_frigate("front_doorbell", "doorbell")
          self.turn_on("input_boolean.doorbell_pressed")
          self.listen_for_reset_doorbell_pressed = self.listen_event(self.reset_doorbell_pressed_flag, "reset_doorbell_pressed_flag", oneshot=True)
  
  # System has booted.
  def on_doorphone_system_up(self, entity, attribute, old, new, kwargs):
    doorphone_up_message = "Doorphone System Up: " + str(old)
    reboot_snapshot_file = self.camera_image_path + "doorphone_bootup_picture.jpg"
    #self.call_service("python_script/set_state", entity_id = self.doorphone_event_type, state = "0")
    self.set_state(self.doorphone_event_type, state = '0')
    is_it_reboot_time = self.get_state(globals.doorphone_reboot_time_sensor)
    self.log("Reboot time sensor: " + str(is_it_reboot_time))
    if is_it_reboot_time == "on":
      self.log("Sending email.")
      self.call_service("notify/email_max", title = "Door Phone Alert (Door Phone Up).", message = doorphone_up_message)
    else:
      #self.run_in(self.get_latest_camera_picture, 10, image_url = self.camera_image_url, image_filename = reboot_snapshot_filename)
      self.take_picture(camera_location = self.camera_location, picture_type = "reboot", picture_caption = "Doorphone rebooted.")
      #self.run_in(self.cctv_library.get_latest_camera_picture, 10, image_filename = reboot_snapshot_file, image_url = self.camera_image_url)
      #self.call_service("notify/email_max", title = "Door Phone Alert (Door Phone Up).", message = doorphone_up_message)
      #self.call_service("telegram_bot/send_photo", file = reboot_snapshot_file, caption = doorphone_up_message)
  
  # When doorphone drops off network:
  def on_doorphone_dropped_off_network(self, entity, attribute, old, new, kwargs):
    self.log("Door Phone no ping.")
    is_it_reboot_time = self.get_state(globals.doorphone_reboot_time_sensor)
    if is_it_reboot_time == "on":
      self.log("Door Phone is within daily reboot period.")
    else:
      self.log("Door Phone has stopped responding to pings.")
      self.call_service(globals.max_telegram, title = "Doorphone Ping Alert.", message = "Doorphone has dropped off the network.")
  
  def on_porch_light_timer_finished(self, event, data, kwargs):
    self.log("Porch light timer finished.")
    self.log("kwargs:")
    self.log(kwargs)
    return_brightness = kwargs["old_brightness"]
    self.log(return_brightness)
    self.turn_on(globals.porch_light, brightness=return_brightness, transition=10)

  # Tamper Alarm Activated.
  def on_doorphone_tamper(self, entity, attribute, old, new, kwargs):
    self.log("Door Phone Tamper Alarm.")
    #self.call_service("python_script/set_state", entity_id = self.doorphone_event_type, state = "0")
    self.set_state(self.doorphone_event_type, state = '0')
    self.take_picture(camera_location = self.camera_location, picture_type = "tamper", picture_caption = "Front Door Tamper Alarm.")
    self.call_service(globals.max_app, title = "Front Door Tamper Alarm!",\
                                       message = "Tamper Alarm Activated at Front (Click to view camera).",\
                                       data = {"channel":"Front_Door","tag":"Tamper", "clickAction": globals.lovelace_cctv_tab})

  # Person detected on front camera (Frigate Sensor).
  def on_person_at_front_new(self, entity, attribute, old, new, kwargs):
    self.log("Person at front (Door Phone New).")
    event_picture = self.get_state("camera.front_doorbell_person", attribute = "entity_picture")
    self.log("HA URL: " + str(globals.home_assistant_url))
    event_picture_url = "https://" + globals.home_assistant_url + event_picture
    self.log("Event Picture: " + event_picture_url)
    if self.get_state(globals.front_doorbell_person_detection_switch) == "on":  # Switch off alerts if they get annoying.
      snapshot_filename = self.cctv_library.get_picture_from_frigate("front_doorbell", "person")
      self.log("Snapshot filename: " + str(snapshot_filename))
      self.log("Door phone person at front (new), sending message.")
      if self.get_state("binary_sensor.internet_down") == "on":
        self.call_service(globals.max_telegram, title = "Person at front.", message = "Person at Front (new Doorphone version).")
        self.call_service("telegram_bot/send_photo", file = self.latest_camera_image, caption = "Person at front.")
        #self.log("URL: " + str(event_picture_url))
        #self.call_service("telegram_bot/send_photo", url = event_picture_url, caption = "Person at front.(Doorphone)")
        self.call_service(globals.max_app, title = "Doorphone Alert (New)",\
                                           message = "Person Detected at Front (Click to view camera).",\
                                           data = {"channel":"Front_Door",\
                                                   "tag":"Person",\
                                                   "image":event_picture_url,\
                                                   "clickAction": globals.lovelace_cctv_tab })
      else:
        self.call_service("notify/max_sms", message = "Person detected at front door (no internet).")
    else:
      self.log("Person detection is switched off.")

  
  def on_doorphone_power_off(self, entity, attribute, old, new, kwargs):
    self.log("Doorphone PSU Powered off.")
    self.turn_on(globals.doorphone_power_poe_injector)
    self.log("Doorphone PSU Powered back on.")

  ###############################################################################################################
  # Other functions:
  ###############################################################################################################

  # Doorphone has rebooted.
  def system_rebooted(self):
    reboot_title = "Door Phone Alert (Reboot)."
    reboot_message = "Door Phone System Rebooted."
    self.log(reboot_message)
    #self.call_service("python_script/set_state", entity_id = self.doorphone_event_type, state = "0")  # Retired.
    self.set_state(self.doorphone_event_type, state = '0')
    is_it_reboot_time = self.get_state(globals.doorphone_reboot_time_sensor)
    if is_it_reboot_time == "on":  # Nightly reboot, just send an email.
      self.log("Nightly reboot, not sending notification.")
      self.call_service("notify/email_max", title = reboot_title, message = reboot_message)
    else:
      self.call_service(globals.notify_max_all, title = reboot_title, message = reboot_message)

  # Take a picture and send it (by Telegram).
  def take_picture(self, camera_location, picture_type, picture_caption):
    self.log("Take picture: " + picture_type)
    timed_snapshot_filename, snapshot_filename = self.cctv_library.get_picture_from_frigate(self.camera_location, picture_type)
    #self.call_service("telegram_bot/send_photo", file = snapshot_filename, caption = picture_caption)
    self.cctv_library.get_picture_from_frigate("front_doorbell", picture_type)
    self.call_service("telegram_bot/send_photo", target = globals.telegram_chat_id, caption = "Front Door", file = snapshot_filename)


  def reset_doorbell_pressed_flag(self, event_name, data, kwargs):
    self.log("Doorbell Pressed Reset Flag.")
    self.turn_off("input_boolean.doorbell_pressed")

  def disable_alert(self, kwargs):
    self.log("Alert disabled.")

   # Motion detected on internal motion detector.
  def motion_detected(self):
    #self.log("Motion detected.")
    motion_detected = "1"
    self.call_service("timer/start", entity_id = globals.frontdoor_motion_timer)

  
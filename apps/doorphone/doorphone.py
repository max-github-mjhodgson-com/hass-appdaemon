# Doorphone automations for Grandstream SIP doorphone.
#
# Uses websocket triggers configured in Home Assistant.
# Also uses Frigate for the CCTV.
#
# Max Hodgson 2022

import appdaemon.plugins.hass.hassapi as hass
import time, requests
from datetime import timedelta
from datetime import datetime
import globals


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
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    global camera_location
    camera_location = "front_doorbell"
    global camera_image_url  # Uses http as it is on the internal network.
    camera_image_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/"+ camera_location +"/latest.jpg"
    global camera_image_path
    camera_image_path = "/config/media/cctv/" + camera_location + "/tmp/"
    global camera_image_name
    camera_image_name = camera_image_path + camera_location + "_latest.jpg"

    self.mqtt = self.get_plugin_api("MQTT")

    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")

    global GarageLibrary
    GarageLibrary = self.get_app("garage")

    global CCTVLibrary
    CCTVLibrary = self.get_app("cctv")

    global AsteriskComms # To do.
    AsteriskComms = self.get_app("asterisk_comms")
    # Example: AsteriskComms.hangup(globals.doorphone_extension_number)

    global doorphone_event_type
    doorphone_event_type = "sensor.doorphone_event_type"

    global doorphone_message_title
    doorphone_message_title = "Door Phone Alert"

    #global last_ring 
    self.last_ring = datetime.now() - timedelta(seconds = 35)
    #global lovelace_cctv_tab
    #lovelace_cctv_tab = "/lovelace/10"
    #self.take_picture("front_doorbell", "doorphone", "test")
    #CCTVLibrary.take_picture(camera_location = "front_doorbell", picture_type = "doorbell", picture_caption = "Test.")
    #self.run_in(CCTVLibrary.get_latest_camera_picture, 1, image_url = camera_image_url, image_filename = "/config/tmp/test.jpg")
    #CCTVLibrary.get_latest_camera_picture( image_url = camera_image_url, image_filename = "/config/tmp/test.jpg")

    # State monitors
    new_event = self.listen_state(self.on_event_detected, doorphone_event_type, old = "0")
    card_used = self.listen_state(self.on_doorphone_card_used, doorphone_event_type, new = "600")
    system_up = self.listen_state(self.on_doorphone_system_up, doorphone_event_type, new = "1101")
    
    doorbell_button_handler01 = self.listen_state(self.on_doorphone_doorbell_button_pressed, doorphone_event_type, new = "500")
    doorbell_button_handler02 = self.listen_state(self.on_doorphone_doorbell_button_pressed, doorphone_event_type, new = "501")
    doorbell_button_handler03 = self.listen_state(self.on_doorphone_doorbell_button_pressed, doorphone_event_type, new = "504")
    doorbell_button_handler04 = self.listen_state(self.on_doorphone_doorbell_button_pressed, doorphone_event_type, new = "502")
    doorbell_button_handler05 = self.listen_state(self.on_doorphone_tamper, doorphone_event_type, new = "1100")
    # Disabled 12Jan23 person_at_front = self.listen_state(self.on_person_at_front, "image_processing.doods_front_door", old = "0")
    person_at_front_frigate = self.listen_state(self.on_person_at_front_new, "binary_sensor.front_doorbell_person_motion", new = "on")
    doorphone_poe_power_handler = self.listen_state(self.on_doorphone_power_off, globals.doorphone_power_poe_injector, new = "off", duration = 10)
    doorphone_ping_sensor_handler = self.listen_state(self.on_doorphone_dropped_off_network, "binary_sensor.door_phone", new = "off", duration = 10)
    
    # Event monitors:
    self.motion_timer_finished_handler = self.listen_event(self.on_motion_undetected, "timer.finished", entity_id = globals.frontdoor_motion_timer)
    self.mqtt.listen_event(self.on_mqtt_message_received_event, "MQTT_MESSAGE", topic="frigate/events")
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
    #self.call_service("python_script/set_state", entity_id = doorphone_event_type, state = "0") ## Retired.
    self.set_state(doorphone_event_type, state='0')
    #self.call_service("python_script/set_state", entity_id = "sensor.doorphone_card_number", state = "0")
    self.set_state("sensor.doorphone_card_number", state='0')
    self.log("Card used: %s", card_number)
    self.call_service(globals.notify_max_all, title = "Door Phone Alert", message = "Card used.")
    caption_text = "Doorbell Card Used: "+card_number
    self.take_picture(camera_location = camera_location, picture_type="card", picture_caption = caption_text)
    
    if card_number in globals.cards_garage_door:
      self.log("Card number found in Garage Door List.")
      self.call_service(globals.notify_max_all, title = "Door Phone Alert", message = "Card used: Garage Door Open.")
      door_state = self.get_state(globals.garage_door_entity)
      self.log(door_state)
      if door_state == "closed":
        self.log("Garage is closed, opening.")
        GarageLibrary.power_on_and_open_garage()
      else:
        self.log("Garage is open, closing.")
        GarageLibrary.close_garage_and_power_off()

  # Doorbell button has been pressed.
  def on_doorphone_doorbell_button_pressed(self, entity, attribute, old, new, kwargs):
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
        self.take_picture(camera_location = camera_location, picture_type = "doorbell", picture_caption = "Doorbell Button Pressed (API).")
        self.turn_on("input_boolean.doorbell_pressed")
        self.listen_for_reset_doorbell_pressed = self.listen_event(self.reset_doorbell_pressed_flag, "reset_doorbell_pressed_flag", oneshot=True)
  
  # System has booted.
  def on_doorphone_system_up(self, entity, attribute, old, new, kwargs):
    doorphone_up_message = "Doorphone System Up."
    reboot_snapshot_filename = camera_image_path + "doorphone_bootup_picture.jpg"
    #self.call_service("python_script/set_state", entity_id = doorphone_event_type, state = "0")
    self.set_state(doorphone_event_type, state = '0')
    if self.now_is_between("01:29:00", "01:35:00"):  # Nightly reboot, just send an email.
      self.log("Sending email.")
      #self.call_service("notify/email_max", title = "Door Phone Alert (Door Phone Up).", message = doorphone_up_message)
    else:
      #self.run_in(self.get_latest_camera_picture, 10, image_url = camera_image_url, image_filename = reboot_snapshot_filename)
      self.run_in(CCTVLibrary.get_latest_camera_picture, 10, image_url = camera_image_url, image_filename = reboot_snapshot_filename)
      self.run_in(self.take_reboot_picture, 20, doorphone_up_message = doorphone_up_message, reboot_snapshot_filename = reboot_snapshot_filename)
  
  # When doorphone drops off network:
  def on_doorphone_dropped_off_network(self, entity, attribute, old, new, kwargs):
    self.log("Doorphone no ping.")
    if self.now_is_between(globals.reboot_start_time, globals.reboot_end_time):
      self.log("Doorphone is within daily reboot period")
    else:
      self.log("Doorphone has stopped responding to pings.")
      self.call_service(globals.max_telegram, title = "Doorphone Ping Alert.", message = "Doorphone has dropped off the network.")

  def on_mqtt_message_received_event(self, eventname, data, *args):
  # http://192.168.101.5:8123/api/frigate/notifications/1658731657.459786-3jnewn/snapshot.jpg
    #self.log("MQTT New Version")
    true = 1
    false = 0
    null = "null"
    media_base_path = globals.cctv_media_location
    video_base_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/events/"
    payload = eval(data['payload'])
    #event_camera = data['topic']['before']['camera']
    #event_label = data['topic']['before']['label']
    #self.log("Payload: " + str(payload))
    event_id_before = payload['before']['id']
    event_id_after = payload['after']['id']
    event_label_before = payload['before']['label']
    event_label_after = payload['after']['label']
    #event_entered_zones = payload['after']['entered_zones']
    event_type = payload['type']
    self.log("Before ID: " + event_id_before)
    self.log("After ID: " + event_id_after)
    self.log("Event Type: " + event_type)
    #self.log("Entered Zones" + str(event_entered_zones))
    #picture_url = "http://localhost:8123/api/frigate/notifications/"
    picture_url = "http://192.168.101.5:8123/api/frigate/notifications/"
    if event_label_before == "person":
      if event_type == "new":
        self.log("Sending start image.(New Version)")
        picture_url_begin = picture_url + event_id_before + "/snapshot.jpg"
        self.log("Image URL: " + picture_url_begin)
        self.call_service("telegram_bot/send_photo", url = picture_url_begin, caption = "Person at front (New Version).")
        self.call_service(globals.max_app, title = "Doorphone Alert (New)",\
                                           message = "Person at Front Door",\
                                           data = {"channel":"Front_Door",\
                                                    "clickAction":globals.lovelace_cctv_tab ,\
                                                    "image": picture_url_begin})
      if event_type == "end":
        self.log("Sending end image.")
        picture_url_end = picture_url + event_id_after + "/snapshot.jpg"
        video_url = video_base_url + event_id_after + "/clip.mp4"
        # Todo: Store a latest picture in the media directory. 
        self.call_service("telegram_bot/send_photo", disable_notification = "yes", url = picture_url_end, caption = video_url)
        #self.call_service("telegram_bot/send_video", disable_notification = "yes", timeout = "yes", url = video_url, caption = "Person at front (video clip).")
    # + event_camera + event_label)
    #event_type = data['topic']['after']['type']
    #self.log(event_type)
  
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
    #self.call_service("python_script/set_state", entity_id = doorphone_event_type, state = "0")
    self.set_state(doorphone_event_type, state = '0')
    self.take_picture(camera_location = camera_location, picture_type = "tamper", picture_caption = "Front Door Tamper Alarm.")
    self.call_service(globals.max_app, title = "Front Door Tamper Alarm!",\
                                       message = "Tamper Alarm Activated at Front (Click to view camera).",\
                                       data = {"channel":"Front_Door","tag":"Tamper", "clickAction": globals.lovelace_cctv_tab})

  # Person detected on front camera (Frigate Sensor).
  def on_person_at_front_new(self, entity, attribute, old, new, kwargs):
    #snapshot_filename = globals.cctv_media_location+"/frontdoor/latest/frontdoor_person.jpg"
    self.log("Person at front (new).")
    #self.log(attribute)
    if self.get_state(globals.front_doorbell_person_detection_switch) == "on":  # Switch off alerts if they get annoying.
      self.call_service(globals.max_telegram, title = "Person at front (new)", message = "Person at Front (new).")
      #self.call_service("telegram_bot/send_photo", file = snapshot_filename, caption = "Person at front.")
      self.call_service(globals.max_app, title = "Doorphone Alert (New)",\
                                         message = "Person Detected at Front (Click to view camera).",\
                                         data = {"channel":"Front_Door", "tag":"Person", "clickAction": lovelace_cctv_tab })
    else:
      self.log("Person detection is switched off.")

  def on_person_at_front(self, entity, attribute, old, new, kwargs):  # Retired as Frigate does this now.
    self.log("Person at front. Old")
    if self.get_state("input_boolean.person_detection_frontdoor") == "on":
      test_attribute = self.get_state(str(entity), attribute="matches")
      coord2 = test_attribute["person"][0]["box"][2]
      coord1 = test_attribute["person"][0]["box"][0]
      coord_total = coord2 - coord1
      #self.log(test_attribute)
      #self.log("Coord total:")
      #self.log(coord_total)
      snapshot_filename = globals.cctv_media_location + "/" + camera_location + "/latest/frontdoor_person.jpg"
      if coord_total < 0.3:
        self.log("Person detect area is too small.")
      else:
        self.log("Person detected is the correct size.")
        self.call_service("telegram_bot/send_photo", file = snapshot_filename, caption = "Person at front.")
        self.call_service(globals.max_app, title = "Doorphone Alert (Old)",\
                                         message = "Person Detected at Front (Click to view camera).",\
                                         data = {"channel":"Front_Door", "tag":"Person", "clickAction": lovelace_cctv_tab })
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
    #self.call_service("python_script/set_state", entity_id = doorphone_event_type, state = "0")  # Retired.
    self.set_state(doorphone_event_type, state = '0')
    if self.now_is_between("01:29:00", "01:35:00"):  # Nightly reboot, just send an email.
      self.log("Nightly reboot, not sending notification.")
      #self.call_service("notify/email_max", title = reboot_title, message = reboot_message)  # Email in Home Assistant isn't currently working.
    else:
      self.call_service(globals.notify_max_all, title = reboot_title, message = reboot_message)

  # Take a picture and send it (by Telegram).
  def take_picture(self, camera_location, picture_type, picture_caption):
    self.log("Take picture: " + picture_type)
    timed_snapshot_filename, snapshot_filename = CCTVLibrary.get_picture_from_frigate("front_doorbell", picture_type = "doorbell")
    self.call_service("telegram_bot/send_photo", file = snapshot_filename, caption = picture_caption)

  def reset_doorbell_pressed_flag(self, event_name, data, kwargs):
    self.log("Doorbell Pressed Reset Flag.")
    self.turn_off("input_boolean.doorbell_pressed")

  def take_reboot_picture(self, kwargs):
    doorphone_up_message = kwargs["doorphone_up_message"]
    reboot_snapshot_filename = kwargs["reboot_snapshot_filename"]
    CCTVLibrary.get_latest_camera_picture( image_url = camera_image_url, image_filename = reboot_snapshot_filename)
    #self.call_service("notify/email_max", title = "Door Phone Alert (Door Phone Up).", message = doorphone_up_message)
    self.call_service("telegram_bot/send_photo", file = reboot_snapshot_filename, caption = doorphone_up_message)

  def disable_alert(self, kwargs):
    self.log("Alert disabled.")

   # Motion detected on internal motion detector.
  def motion_detected(self):
    #self.log("Motion detected.")
    motion_detected = "1"
    self.call_service("timer/start", entity_id = globals.frontdoor_motion_timer)

  
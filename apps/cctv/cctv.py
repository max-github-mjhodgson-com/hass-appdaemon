# CCTV App
# Max Hodgson 2023
# Version: 10052023.01
#
# Requires: Frigate, MQTT
#
import appdaemon.plugins.hass.hassapi as hass

import os
import requests
import time

import globals_module as globals

#from datetime import timedelta
from datetime import datetime

class Cctv(hass.Hass):

  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    self.mqtt = self.get_plugin_api("MQTT")
    
    #Set up some variables:
    self.frigate_camera_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/"  #+ camera_location +"/latest.jpg"
    
    #self.set_value(globals.front_motion_detection_off_input_number, 0)

    # Load external app libraries:
    self.function_library = self.get_app("function_library")

    # State monitors:
    # Switch person detection back on after a hour.
    self.person_detection_switch_on_handler = self.listen_state(self.on_switch_on_person_detection, globals.front_doorbell_person_detection_switch, old = "on", new = "off", duration = 3600)

    # Event monitors:
    self.mqtt.listen_event(self.on_mqtt_message_received_event, "MQTT_MESSAGE", topic="frigate/events")
    self.listen_state(self.on_front_motion_detect_on_off, globals.front_motion_detection_off_input_number)
    self.listen_state(self.on_front_motion_detect_on_off, globals.front_doorbell_person_detection_switch)
    sunset_time_handler = self.run_at_sunset(self.run_sunset_tasks)


###############################################################################################################
  # Callback functions:
###############################################################################################################

  def on_switch_on_person_detection(self, entity, attribute, old, new, kwargs):
    self.log("Switch back on person detection after timeout.")
    self.turn_on(globals.front_doorbell_person_detection_switch)

  def on_mqtt_message_received_event(self, eventname, data, *args):
  # http://<URL>:8123/api/frigate/notifications/1658731657.459786-3jnewn/snapshot.jpg
    self.log("MQTT (CCTV App)")
    true = 1  # Do not remove.
    false = 0  # Do not remove.
    null = "null"
    media_base_path = globals.cctv_media_location
    #video_base_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/events/"
    video_base_url = "https://" + globals.frigate_external_hostname + "/api/events/"
    picture_url = "http://" + globals.home_assistant_url + ":8123/api/frigate/notifications/"
    payload = eval(data['payload'])
    #event_camera = data['topic']['before']['camera']
    #event_label = data['topic']['before']['label']
    self.log("Payload: " + str(payload))
    event_id_before = payload['before']['id']
    event_id_after = payload['after']['id']
    event_label_before = payload['before']['label']
    event_label_after = payload['after']['label']
    event_entered_zones_before = payload['before']['entered_zones']
    event_number_of_entered_zones_before = len(event_entered_zones_before)
    event_entered_zones_after = payload['after']['entered_zones']
    event_type = payload['type']
    self.log("Before ID: " + event_id_before)
    self.log("After ID: " + event_id_after)
    self.log("Event Type: " + event_type)
    self.log("Object Type: " + str(event_label_after))
    if event_number_of_entered_zones_before > 0 and event_type != "":
      self.log("Entered Zones: " + str(event_entered_zones_before))
      self.send_an_alert(zone = event_entered_zones_before, detected_object = event_label_after)
    else:
      self.log("No zones were entered.")
    if event_label_before == "person":
      if event_type == "new":
        self.log("Sending start image.(New Version, via telegram.)")
        picture_url_begin = picture_url + event_id_before + "/snapshot.jpg"
        self.log("Image URL: " + picture_url_begin)
        if self.get_state(globals.front_doorbell_person_detection_switch) == "on":
          self.call_service("telegram_bot/send_photo", url = picture_url_begin, caption = "Person at front (New Version).")
          self.call_service(globals.max_app, title = "Doorphone Alert (New)",\
                                             message = "Person at Front Door",\
                                             data = {"channel":"Front_Door",\
                                                     "clickAction":globals.lovelace_cctv_tab ,\
                                                     "image": picture_url_begin})
          self.call_service("device_tracker/see", dev_id = globals.max_phone_tracker)
      if event_type == "end":
        self.log("Sending end image (via telegram).")
        picture_url_end = picture_url + event_id_after + "/snapshot.jpg"
        self.log("picture_url_end: " + str(picture_url_end))
        video_url = video_base_url + event_id_after + "/clip.mp4"
        self.log("video_url: " + str(video_url))
        # Todo: Store a latest picture in the media directory.
        front_door_detection_switch_status = self.get_state(globals.front_doorbell_person_detection_switch)
        if front_door_detection_switch_status == "on":
          self.log("Detection switch status (end image): " + str(front_door_detection_switch_status))
          self.call_service("telegram_bot/send_photo", disable_notification = "yes", url = picture_url_end, caption = video_url)
          #self.call_service("telegram_bot/send_video", disable_notification = "yes", timeout = "yes", url = video_url, caption = "Person at front (video clip).")
          self.call_service(globals.max_app, title = "Doorphone Alert (New) end image",\
                                             message = "Person at Front Door",\
                                             data = {"channel":"Front_Door",\
                                                     "clickAction":globals.lovelace_cctv_tab ,\
                                                     "image": picture_url_end})
    # + event_camera + event_label)
    #event_type = data['topic']['after']['type']
    #self.log(event_type)

  def on_front_motion_detect_on_off(self, entity, attribute, old, new, cb_args):
    self.log("Motion detect off select.")
    self.log("Entity: " + str(entity))
    self.log("New: " + str(new))
    if old not in ["unavailable"]:
      if entity == globals.front_doorbell_person_detection_switch:
        self.log("Detection switch activated.")
        self.camera_object_detect_on_off("front_doorbell", new)
      elif entity == globals.front_motion_detection_off_input_number:
        self.log("Detection minute timer activated.")

  def run_sunset_tasks(self, kwargs):
    self.turn_on(globals.front_doorbell_person_detection_switch)

###############################################################################################################
  # Other functions:
###############################################################################################################

 # Take a picture.
  def get_picture_from_frigate(self, camera_id, picture_type):   #, picture_caption):
    #self.log("Take picture: " + picture_type)
    snapshot_filename = globals.cctv_media_location + "/" + camera_id + "/latest/" + camera_id + "_" + picture_type + ".jpg"
    image_timestamp = datetime.strftime(self.datetime(), '%Y%m%d_%H%M%S')
    directory_datestamp = datetime.strftime(self.datetime(), '%Y/%b/%d-%a')
    picture_filename =  camera_id + "_" + picture_type + "." + image_timestamp + ".jpg"
    picture_directory = globals.cctv_media_location + "/" + camera_id +"/" + directory_datestamp
    os.makedirs(picture_directory)
    #timed_snapshot_filename = globals.cctv_media_location + "/" + camera_id +"/" + directory_datestamp + "/" + camera_id + "_" + picture_type + "." + image_timestamp + ".jpg"
    timed_snapshot_filename = picture_directory + "/" + picture_filename
    self.get_latest_camera_picture(image_url = self.frigate_camera_url + camera_id + "/latest.jpg", image_filename = timed_snapshot_filename)
    self.get_latest_camera_picture(image_url = self.frigate_camera_url + camera_id + "/latest.jpg", image_filename = snapshot_filename)
    return timed_snapshot_filename, snapshot_filename

  def get_latest_camera_picture(self, image_url, image_filename):
    self.log("Get latest camera picture.")
    img_data = requests.get(image_url).content
    with open(image_filename, 'wb') as handler:
      handler.write(img_data)

  def send_an_alert(self, **kwargs):
    #self.log("Send an alert.")
    alert_switch_status = self.get_state(globals.front_doorbell_person_detection_switch)
    #self.log("Alert switch status: " + str(alert_switch_status))
    if self.get_state(alert_switch_status) == "on":
      self.log("Sending an alert.")
      self.log("Kwargs: " + str(kwargs))
      #event = kwargs["event_id"]
      zone = kwargs["zone"]
      object = kwargs["detected_object"]
      #self.log("Event ID: " +str(event))
      self.log("Zone(s) entered: " + str(zone))
      self.log("Detected object: " + str(object))

  def camera_object_detect_on_off(self, camera_name, detect_state):
    self.log("Switching camera object detection: " + str(detect_state) + "for camera: " + str(camera_name))
    frigate_camera_id = "frigate/" + camera_name + "/detect/set"
    self.mqtt.mqtt_publish(frigate_camera_id, detect_state.upper(), namespace = "mqtt")

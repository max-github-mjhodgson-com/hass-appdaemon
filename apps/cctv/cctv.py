# CCTV App
# Max Hodgson 2023

import appdaemon.plugins.hass.hassapi as hass
import time, requests
from datetime import timedelta
from datetime import datetime
import globals

class Cctv(hass.Hass):

  def initialize(self):
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    self.mqtt = self.get_plugin_api("MQTT")

    #Set up some variables:
    global frigate_camera_url
    frigate_camera_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/"  #+ camera_location +"/latest.jpg"

    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")

    # State monitors:
    person_detection_switch_handler = self.listen_state(self.switch_on_person_detection, globals.front_doorbell_person_detection_switch, old = "on", new = "off", duration = 3600)

    # Event monitors:
    self.mqtt.listen_event(self.on_mqtt_message_received_event, "MQTT_MESSAGE", topic="frigate/events")
  
###############################################################################################################
  # Callback functions:
###############################################################################################################

  def switch_on_person_detection(self, entity, attribute, old, new, kwargs):
    self.log("Switch on person detection.")
    self.turn_on(globals.front_doorbell_person_detection_switch)

  def on_mqtt_message_received_event(self, eventname, data, *args):
  # http://192.168.101.5:8123/api/frigate/notifications/1658731657.459786-3jnewn/snapshot.jpg
    self.log("MQTT New Version")
    true = 1
    false = 0
    null = "null"
    media_base_path = globals.cctv_media_location
    video_base_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/events/"
    payload = eval(data['payload'])
    #event_camera = data['topic']['before']['camera']
    #event_label = data['topic']['before']['label']
    self.log("Payload: " + str(payload))
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


###############################################################################################################
  # Other functions:
###############################################################################################################

 # Take a picture.
  def get_picture_from_frigate(self, camera_id, picture_type):   #, picture_caption):
    #self.log("Take picture: " + picture_type)
    snapshot_filename = globals.cctv_media_location + "/" + camera_id + "/latest/" + camera_id + "_" + picture_type + ".jpg"
    #self.log(snapshot_filename)
    image_timestamp = datetime.strftime(self.datetime(), '%Y%m%d_%H%M%S')
    directory_datestamp = datetime.strftime(self.datetime(), '%Y/%b/%d-%a')
    timed_snapshot_filename = globals.cctv_media_location + "/" + camera_id +"/" + directory_datestamp + "/" + camera_id + "_" + picture_type + "." + image_timestamp + ".jpg"
    #self.log(timed_snapshot_filename)
    self.get_latest_camera_picture(image_url = frigate_camera_url + camera_id + "/latest.jpg", image_filename = timed_snapshot_filename)
    self.get_latest_camera_picture(image_url = frigate_camera_url + camera_id + "/latest.jpg", image_filename = snapshot_filename)
    return timed_snapshot_filename, snapshot_filename

  def get_latest_camera_picture(self, kwargs):
    #self.log("Get latest camera picture.")
    #self.log("kwargs:")
    #self.log(kwargs)
    image_url = kwargs["image_url"]
    image_filename = kwargs["image_filename"]
    img_data = requests.get(image_url).content
    with open(image_filename, 'wb') as handler:
      handler.write(img_data)

    
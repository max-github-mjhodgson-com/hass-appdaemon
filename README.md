# hass-appdaemon
This is a repo for my Home Assistant Appdaemon Python code.
I don't use many automations in the Home Assistant Frontend. 99% of my automations are in Appdaemon (due to the complexity).
All of these are under active development and experimentation.

Areas covered are Grandstream SIP Doorphone, CCTV, House Mode, Garage, Calendar, Kitchen, Mobile App Events and Car (using Fordpass).

App Descriptions:

## Doorphone

This app interfaces with a Grandstream GDS3710 SIP Doorphone. Home Assistant receives events from the doorphone via webhooks, This creates a sensor, which can then be monitored. Each event passed from the doorphone carrys an identifier number, for example: 500 for doorbell or 900 for motion detected (using the internal motion detector). The Appdaemon app will action the events and grab pictures (from the camera), send messages, etc.

Example configuration for webhook in Home Assistant configuration.yaml:

```
template:
# example.domain.com/api/webhook/mynicewebhookid
  - trigger: # Doophone.
      - platform: webhook
        webhook_id: mynicewebhookid
    sensor:
      - name: "Doorphone Event Timestamp"
        state: "{{ trigger.data.timestamp }}"
      - name: "Doorphone Event Type"
        state: "{{ trigger.data.type }}"
      - name: "Doorphone Content"
        state: "{{ trigger.data.content }}"
      - name: "Doorphone SIP Number"
        state: "{{ trigger.data.sip }}"
      - name: "Doorphone Card Number"
        state: "{{ trigger.data.card }}"
```

The configuration on the Grandstream looks like this:

<img src="./GDS-Webhook-config.PNG"/>


## CCTV

This listens to a Frigate installation via MQTT and decodes the data it revceives to be able to extract labels, event IDs, zones and objects.

The app utilises an input_boolean in Home Assistant, which can turn off alerts for person detection. Useful for people working in the area of a camera and being flooded with alerts.

## House Mode

This controls the mode that the house is currently in. This is based on an input_select in Home Assistant, the modes are Home, Out (for a short time), Away (for a long time), Sleep, Pre-Arrival, Scheduled arrival, Just Arrived, Just Left and Pre-Departure. It will change modes when people enter or leave, or other modes timeout. It will also run automations based on the current mode.

Home Assistant configuration.yaml for the House Mode "input_select":

```
input_select:
  house_mode_l:
    name: House Mode
    options:
      - Home
      - Out
      - Away
      - Sleep
      - Pre-Arrival
      - Scheduled Arrival
      - Just Arrived
      - Just Left
      - Pre-Departure
```

## Kitchen

This currently controls the kettle. It will watch the the power level to reach a certain threshold. This will then start a short timer (to switch the plug off) and send a Telegram message.


## Mobile App Events

This listens to events from the Home Assistant Mobile App. Mainly events like pressing a button on a notification. This will then execute the required response through a linked app, such as calling the garage app to close the garage door.


# Hardware Setup

Reference hardware:

- Raspberry Pi 4 / 5
- Adafruit RGB Matrix HAT
- 64×64 HUB75 RGB LED panel, typically 1/32 scan
- Dedicated 5V panel power supply

## Wiring

This setup follows the official guide from Adafruit:  
https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi/matrix-setup

1. Mount the RGB Matrix HAT on the Raspberry Pi GPIO header.
2. Power the panel from a dedicated 5V supply.

<img src="https://cdn-learn.adafruit.com/assets/assets/000/051/027/medium640/led_matrices_leds_plugspades.jpg?1518646189" width="500"/>

3. Connect the HUB75 ribbon cable.

<img src="https://cdn-learn.adafruit.com/assets/assets/000/051/028/medium640/led_matrices_leds_plugidc.jpg?1518646614" width="500"/>

4. Ensure a common ground between the panel, HAT, and Raspberry Pi.

> **Important:** Do not power the LED panel directly from the Raspberry Pi.

## E-line fix

Some 64×64 panels require the E address line to be routed to GPIO8. Incorrect E-line configuration can cause duplicated rows or distorted output.

<img src="https://cdn-learn.adafruit.com/assets/assets/000/063/008/medium640/led_matrices_addr-e-pad.jpg?1538677495" width="500"/>


## Raspberry Pi audio

The project setup disables `snd_bcm2835` because it can interfere with low-level matrix timing. The Raspberry Pi OS boot configuration path differs between OS versions, so verify the correct path for the installed release before changing it.

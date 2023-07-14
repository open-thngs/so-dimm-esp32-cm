import gpio
import i2c


main:
  bus := i2c.Bus
    --sda=gpio.Pin 11
    --scl=gpio.Pin 12

  gpioExpanderA := bus.device 0x20
  gpioExpanderB := bus.device 0x21
  
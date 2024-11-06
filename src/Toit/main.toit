import gpio
import i2c

main:
  bus := i2c.Bus
    --sda=gpio.Pin 9
    --scl=gpio.Pin 10

  gpioExpanderA := bus.device 0x20
  gpioExpanderB := bus.device 0x21
  
  print bus.scan
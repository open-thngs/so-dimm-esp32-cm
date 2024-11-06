import gpio
import i2c
import spi


main:
  bus := i2c.Bus
    --sda=gpio.Pin 11
    --scl=gpio.Pin 12

  gpioExpanderA := bus.device 0x20
  gpioExpanderB := bus.device 0x21
  
  print bus.scan

  v0spibus := spi.Bus
    --miso=gpio.Pin 1
    --mosi=gpio.Pin 3
    --clock=gpio.Pin 2

  v0device := v0spibus.device
    --cs=gpio.Pin 4
    --frequency=10_000_000

  // v1spibus := spi.Bus
  //   --miso=gpio.Pin 5
  //   --mosi=gpio.Pin 6
  //   --clock=gpio.Pin 7

  // v1device := v1spibus.device
  //   --cs=gpio.Pin 8
  //   --frequency=10_000_000


  v0device.write #[0x00, 0x00, 0xFF, 0x02, 0xD4, 0xFD, 0x00]
  reading := v0device.read 4
  print "Reading: " + reading.to-string
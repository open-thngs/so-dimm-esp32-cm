import .driver.pca9745b
import spi
import gpio

class LED:
  static RED   ::= #[255, 0, 0, 0]
  static GREEN ::= #[0, 255, 0, 0]
  static BLUE  ::= #[0, 0, 255, 0]
  static WHITE ::= #[0, 0, 0, 255]

  static LED1_ ::= [3,2,1,0]
  static LED2_ ::= [7,6,5,4]
  static LED3_ ::= [11,10,9,8]
  static LED4_ ::= [15,14,13,12]
  static ALL_LED_ ::= [LED1_, LED2_, LED3_, LED4_]

  pca9745b_/PCA9745B

  constructor:
    bus := spi.Bus
        --miso=gpio.Pin 34
        --mosi=gpio.Pin 32
        --clock=gpio.Pin 25

    device := bus.device
        --cs=gpio.Pin 4
        --frequency=25_000_000

    pca9745b_ = PCA9745B(device)
    pca9745b_.enable true

  set_color_all color/ByteArray:
    ALL_LED_.do: | led |
      for i := 0; i < 4; i++:
        pca9745b_.set_pwm led[i] color[i]

  set_color led/int color/ByteArray:
    if led < 1 or led > 4:
      print "LED of index $led is not allowed"
      return

    led_ := LED1_
    if led == 1:
      led_ = LED1_
    else if led == 2:
      led_ = LED2_
    else if led == 3:
      led_ = LED3_
    else :
      led_ = LED4_

    for i := 0; i < 4; i++:
      pca9745b_.set_pwm led_[i] color[i]

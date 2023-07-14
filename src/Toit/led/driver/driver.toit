import serial
import spi
import binary
import gpio
import serial 

class PCA9745B:
  static MODE2_ ::= 0x01

  static IREFALL_ ::= 0x41 // output gain for ALL LEDs

  static LED0_ ::= 0x02
  static LED1_ ::= 0x03
  static LED2_ ::= 0x04
  static LED3_ ::= 0x05

  static _CFG_LEDOUT_GROUP ::= 0b11
  static _CFG_LEDOUT_PWM ::= 0b10
  static _CFG_LEDOUT_OFF ::= 0b00
  static _CFG_LEDOUT_ON ::= 0b01

  static PWMLEDBASE_ ::= 0x08

  registers_/spi.Registers
  device_/spi.Device

  constructor device/spi.Device:
    device_ = device
    registers_ = device.registers
    registers_.set_msb_write true

  enable enable/bool:
    if enable:
      write_ IREFALL_ 0x80
    else:
      write_ IREFALL_ 0x00

  set_pwm led/int value/int:
    if value < 0 or value > 255: return
    if led < 0 or led > 15: return
    write_ (PWMLEDBASE_ + led) value

  set_led0_config value/int:
    write_ LED0_ value

  set_led1_config value/int:
    write_ LED1_ value
  
  set_led2_config value/int:
    write_ LED2_ value

  set_led3_config value/int:
    write_ LED3_ value

  set_led_config_all value/int:
    set_led0_config value
    set_led1_config value
    set_led2_config value
    set_led3_config value

  write_ register/int value/int:
    data := ByteArray 2
    reg := register << 1
    data[0] = reg
    data[1] = value
    device_.transfer data
    debug "Set register 0x$(%02x register) [shifted to 0x$(%02x reg)] to value 0x$(%02x value)"

  read_ register/int:
    data := ByteArray 2
    reg := register << 1 | 0x01
    data[0] = reg
    data[1] = 0xff
    device_.transfer data
    data[0] = 0xff
    device_.transfer data --read=true
    result := data[1]
    debug "Register 0x$(%02x register) [shifted to 0x$(%02x reg)] is: 0x$(%02x result)"
    return result

main:
  bus := spi.Bus
        --miso=gpio.Pin 34
        --mosi=gpio.Pin 32
        --clock=gpio.Pin 25

  device := bus.device
      --cs=gpio.Pin 4
      --frequency=25_000_000

  pca9745b := PCA9745B(device)

  pca9745b.write_ PCA9745B.IREFALL_ 0x80

  for i := 0; i <= 15; i++:
    pca9745b.set_pwm i 0xff
    sleep --ms=100
    //pca9745b.set_pwm i 0x00
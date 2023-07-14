import .led
import pubsub

topic ::= "device:ahl-open"

main:
  led := LED
  led.set_color_all #[255, 0, 0, 0]

  pubsub.subscribe topic: | msg/pubsub.Message |
    print "Received message '$msg.payload.to_string'"
    led.set_color_all #[0, 255, 0, 0]
    sleep --ms=500
    led.set_color_all #[255, 0, 0, 0]

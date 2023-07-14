#include <PI4IOE5V6416.h>

PI4IOE5V6416 e1;
PI4IOE5V6416 e2;

void setup() {
    Serial.begin(115200);
    delay(2000);

    Wire.begin(11, 12);

    e1.attach(Wire, 0x20);
    e1.polarity(PI4IOE5V64XX::Polarity::ORIGINAL_ALL);
    e1.direction(PI4IOE5V64XX::Direction::OUT_ALL);
    e1.write(PI4IOE5V64XX::Level::L_ALL);

    e2.attach(Wire, 0x21);
    e2.polarity(PI4IOE5V64XX::Polarity::ORIGINAL_ALL);
    e2.direction(PI4IOE5V64XX::Direction::OUT_ALL);
    e2.write(PI4IOE5V64XX::Level::L_ALL);

    e1.write(PI4IOE5V64XX::Port::P02, PI4IOE5V64XX::Level::H);
    e1.write(PI4IOE5V64XX::Port::P03, PI4IOE5V64XX::Level::H);

    e1.write(PI4IOE5V64XX::Port::P13, PI4IOE5V64XX::Level::H);  //opener/GPIO27rpi
    Serial.println(e1.read(), BIN);

    //e2.write(PI4IOE5V64XX::Port::P07, PI4IOE5V64XX::Level::H);
    Serial.println(e2.read(), BIN);
}

void loop() {
}


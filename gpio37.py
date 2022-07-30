from periphery import GPIO

solenoid = GPIO("/dev/gpiochip2", 13, "out")  # pin 37

try:
  while True:
    solenoid.write(True)
finally:
  solenoid.write(False)
  solenoid.close()

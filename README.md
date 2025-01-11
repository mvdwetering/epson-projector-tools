# EPSON ESC/VP21 emulator

This is a little emulator so I can develop on the Home Assistant integration without connecting to my real projector for most stuff.

Note that the emulator just provides a "serial" interface over a socket, so connecting from Home Assistant would be to select "Serial" as connection and enter `socket://192.168.178.123:12345` as port. Replace the IP and Port with what you configured.

This emulator is based on the one I made for my Yamaha receiver which can be found here: https://github.com/mvdwetering/ynca

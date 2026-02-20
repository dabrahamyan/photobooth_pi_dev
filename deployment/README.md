To make this work on the pi, add "photobooth.service" to /lib/systemd/system

then in the pi type
sudo systemctl daemon-reload
sudo systemctl enable photobooth.service
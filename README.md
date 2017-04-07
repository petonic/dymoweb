# dymoweb
WebServer to host a simple web page to print labels


## Introduction

It presents a web server on port 5000 of the localhost and prints labels on a Dymo Label-manager.

I use the excellent (and fast) [Perl package to print to Dymo Labelmakers](https://github.com/Firedrake/dymo-labelmanager) by FireDrake (with some local additions of my own to allow for line padding).

## PreReq: Perl Imager module

Install ```curl```, ```cpanm``` and then the ```Imager``` module.

```
sudo apt-get -y install curl gcc-4.7
sudo curl -L http://cpanmin.us | perl - --sudo App::cpanminus
sudo cpanm Imager
```

The last line takes a bit of time to complete, even on an RP3.

Snarfed this advice from https://www.raspberrypi.org/forums/viewtopic.php?f=34&t=13410

## Install Fonts (esp Comic-Sans :-)

```
sudo apt-get -y install ttf-mscorefonts-installer
```

## Configure UDEV and Set Permissions

```
sudo bash -c "cat > /etc/udev/rules.d/50dymo.rules" <<ENDFILE
SUBSYSTEM=="hidraw",
ACTION=="add",
MODE=="0666",
ATTRS{idVendor}=="0922",
ATTRS{idProduct}=="1001",
GROUP="plugdev"
ENDFILE

sudo udevadm control --reload-rules && sudo udevadm trigger

sleep 10

sudo chmod a+rw /dev/hidraw*

```

## Supervisord -- Additional install

* Install supervisord according to [this linked repo](https://github.com/jesperfj/supervisord.git)

* Copy the ```dymoweb.conf``` file to the ```/etc/supervisor/conf.d/``` directory.

* Reboot to get ```supervisord``` working and the dymoweb server working

This will make it so that the web server starts up at boot time and it's monitored, and logged.  Log files are in ```/var/log/dymoweb.{err,out}.log```

## For Wifi, change /boot/wpa_supplicant.

As user:

```
sudo rm -f /boot/wpa_supplicant
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf /boot
sudo ln -s /boot/wpa_supplicant.conf wpa_supplicant.conf
```
This will put the wifi network config file accessible on the /boot partition of the SDCard, which makes it easy for a Mac or PC user to configure.




## Misc

Finished on [2017-03-05 SUN 04:12]

Date             | Description
-----------------|------------
[2017-03-05 SUN 19:25] | Added supervisord config and more README.md documentation.
| [2017-03-05 SUN 20:08]| Added more setup instructions.

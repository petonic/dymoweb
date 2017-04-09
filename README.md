# dymoweb
WebServer to host a simple web page to print labels


It presents a web server on port 80 of the localhost and prints labels on a Dymo Label-manager.

I use the excellent (and fast) [Perl package to print to Dymo Labelmakers](https://github.com/Firedrake/dymo-labelmanager) by FireDrake (with some local additions of my own to allow for line padding).

# One-Time Config Steps for new PI

## For Wifi, change to ```/boot/wpa_supplicant.conf```

We want to make it easy for them to add/configure their wifi password on a headless RPI.  Since most Windows and Macs cannot read Linux file systems, we want to make the wireless security config file to reside on the boot partition, which is a Windows partition.

If they want to then change the WIFI key or add one (because they don't remember it when I initially configure it), they just pop the microSD card in their PC and write that file.

As user:

Make sure that an entry for the new WIFI networks is present in the ```/etc/wpa_supplicant/wpa_supplicant.conf``` file.  An entry looks like one of these (unsecured or secured)

```
network={
	ssid="simunsec"
	key_mgmt=NONE
}

network={
	ssid="Pretty Fly for a WiFi"
	psk="PASSWORDKEY"
	key_mgmt=WPA-PSK
}

```

Here is the script to copy and paste in a terminal (as normal user):

```
sudo rm -f /boot/wpa_supplicant.conf
sudo mv /etc/wpa_supplicant/wpa_supplicant.conf /boot
sudo ln -s /boot/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
```

## Change Hostname

We need to make the change in two files:

* ```/etc/hostname```
* ```/etc/hosts```

Set the following variable, for example:

```
export NEWHOST="newpi"
```

Now copy and paste these lines.

```
sudo sh -c "echo ${NEWHOST} > /etc/host"
sudo sed -i.bak "s/127\.0\.1\.1[ \t]*.*/127.0.1.1\t${NEWHOST}/" /etc/hosts

```

# Building from Source

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

## Misc

Finished on [2017-03-05 SUN 04:12]

Date             | Description
-----------------|------------
[2017-03-05 SUN 19:25] | Added supervisord config and more README.md documentation.
| [2017-03-05 SUN 20:08]| Added more setup instructions.
| [2017-04-09 SUN 09:13] | Added wifi setup instructions

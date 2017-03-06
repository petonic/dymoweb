# dymoweb
WebServer to host a simple web page to print labels

## Introduction

It presents a web server on port 5000 of the localhost and prints labels on a Dymo Label-manager.

I use the excellent (and fast) Perl package https://github.com/Firedrake/dymo-labelmanager by FireDrake (with some local additions of my own to allow for line padding).

## Additional instructions

* Install supervisord according to [the linked repo](https://github.com/jesperfj/supervisord.git)

* Copy the ```dymoweb.conf``` file to the ```/etc/supervisor/conf.d/``` directory.

* Reboot to get ```supervisord``` working and the dymoweb server working

## Misc

Finished on [2017-03-05 SUN 04:12]

* [2017-03-05 SUN 19:25] Added supervisord config and more README.md documentation.
* 

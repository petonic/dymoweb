#!/usr/bin/env python3

# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===
# modified: HappyCodingRobot
#   - added frames, different font styles and command-line parsing with argparse-lib ..
#
# On systems with access to sysfs under /sys, this script will use the three
# variables DEV_CLASS, DEV_VENDOR, and DEV_PRODUCT to find the device file
# under /dev automatically. This behavior can be overridden by setting the
# variable DEV_NODE to the device file path. This is intended for cases, where
# either sysfs is unavailable or unusable by this script for some reason.
# Please beware that DEV_NODE must be set to None when not used, else you will
# be bitten by the NameError exception.


DESCRIPTION = 'Linux Software to print with LabelManager PnP from Dymo\n written in Python'
DEV_CLASS       = 3
DEV_VENDOR      = 0x0922
DEV_PRODUCT     = 0x1002
#DEV_PRODUCT     = 0x1001
DEV_NODE        = None
DEV_NAME        = 'Dymo LabelManager PnP'
#FONT_FILENAME  = '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf'
FONT_CONFIG = {'regular':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-R.ttf',     # regular font
               'bold':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf',        # bold font
               'italic':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-RI.ttf',       # italic font
               'narrow':'/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-C.ttf'    # narrow/condensed
               }
FONT_SIZERATIO  = 7./8
#CONFIG_FILE     = '.dymoprint'
CONFIG_FILE     = 'dymoprint.ini'
VERSION         = "0.3.4 (2016-03-14)"
USE_QR          = True
FONT_FILENAME = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import PIL.ImageOps
import array
import fcntl
import os
import re
import struct
import subprocess
import sys
import termios
import textwrap
import argparse
from configparser import ConfigParser
try:
    from pyqrcode import QRCode
except Exception as e:
    USE_QR = False


class DymoLabeler:
    """Create and work with a Dymo LabelManager PnP object.

    This class contains both mid-level and high-level functions. In general,
    the high-level functions should be used. However, special purpose usage
    may require the mid-level functions. That is why they are provided.
    However, they should be well understood before use. Look at the
    high-level functions for help. Each function is marked in its docstring
    with 'HLF' or 'MLF' in parentheses.
    """

    _ESC = 0x1b
    _SYN = 0x16
    _MAX_BYTES_PER_LINE = 8  # 64 pixels on a 12mm tape

    labelwidth = 0
    labelheight = 0

    def __init__(self, dev):
        """Initialize the LabelManager object. (HLF)"""

        self.cmd = []
        self.response = False
        self.bytesPerLine_ = None
        self.dotTab_ = 0
        self.dev = open(dev, 'r+')

    def sendCommand(self):
        """Send the already built command to the LabelManager. (MLF)"""

        if len(self.cmd) == 0:
            return
        cmdBin = array.array('B', self.cmd)
        cmdBin.tofile(self.dev)
        self.cmd = []
        if not self.response:
            return
        self.response = False
        responseBin = self.dev.read(8)
        response = array.array('B', responseBin).tolist()
        return response

    def resetCommand(self):
        """Remove a partially built command. (MLF)"""

        self.cmd = []
        self.response = False

    def buildCommand(self, cmd):
        """Add the next instruction to the command. (MLF)"""

        self.cmd += cmd

    def statusRequest(self):
        """Set instruction to get the device's status. (MLF)"""

        cmd = [self._ESC, ord('A')]
        self.buildCommand(cmd)
        self.response = True

    def dotTab(self, value):
        """Set the bias text height, in bytes. (MLF)"""

        if value < 0 or value > self._MAX_BYTES_PER_LINE:
            raise ValueError
        cmd = [self._ESC, ord('B'), value]
        self.buildCommand(cmd)
        self.dotTab_ = value
        self.bytesPerLine_ = None

    def tapeColor(self, value):
        """Set the tape color. (MLF)"""

        if value < 0: raise ValueError
        cmd = [self._ESC, ord('C'), value]
        self.buildCommand(cmd)

    def bytesPerLine(self, value):
        """Set the number of bytes sent in the following lines. (MLF)"""

        if value < 0 or value + self.dotTab_ > self._MAX_BYTES_PER_LINE:
            raise ValueError
        if value == self.bytesPerLine_:
            return
        cmd = [self._ESC, ord('D'), value]
        self.buildCommand(cmd)
        self.bytesPerLine_ = value

    def cut(self):
        """Set instruction to trigger cutting of the tape. (MLF)"""

        cmd = [self._ESC, ord('E')]
        self.buildCommand(cmd)

    def line(self, value):
        """Set next printed line. (MLF)"""

        self.bytesPerLine(len(value))
        cmd = [self._SYN] + value
        self.buildCommand(cmd)

    def chainMark(self):
        """Set Chain Mark. (MLF)"""

        self.dotTab(0)
        self.bytesPerLine(self._MAX_BYTES_PER_LINE)
        self.line([0x99] * self._MAX_BYTES_PER_LINE)

    def skipLines(self, value):
        """Set number of lines of white to print. (MLF)"""

        if value <= 0:
            raise ValueError
        self.bytesPerLine(0)
        cmd = [self._SYN] * value
        self.buildCommand(cmd)

    def initLabel(self):
        """Set the label initialization sequence. (MLF)"""

        cmd = [0x00] * 8
        self.buildCommand(cmd)

    def getStatus(self):
        """Ask for and return the device's status. (HLF)"""

        self.statusRequest()
        response = self.sendCommand()
        print (response)

    def create_label(self, text, frame=0):
        """Creates a label and returns the image.  Cannot do anything
        with the image except to call preview(FN)or print(FN)"""
        if not frame == None:
            fontoffset = 0
        else:
            fontoffset = 3

        # create an empty label image
        labelheight = self._MAX_BYTES_PER_LINE * 8
        lineheight = float(labelheight) / len(text)
        fontsize = int(round(lineheight * FONT_SIZERATIO))
        font = ImageFont.truetype(FONT_FILENAME, fontsize)
        labelwidth = max(font.getsize(line)[0] for line in text) + (fontoffset*2)
        labelbitmap = Image.new('1', (labelwidth, labelheight))
        labeldraw = ImageDraw.Draw(labelbitmap)

        # draw frame into empty image
        if frame:
            labeldraw.rectangle(((0,0),(labelwidth-1,labelheight-1)),fill=255)
            labeldraw.rectangle(((fontoffset,fontoffset),(labelwidth-(fontoffset+1),labelheight-(fontoffset+1))),fill=0)

        # write the text into the empty image
        for i, line in enumerate(text):
            lineposition = int(round(i * lineheight))
            labeldraw.text((fontoffset, lineposition), line, font=font, fill=255)
        del labeldraw

        return labelbitmap

    def previewLabel(self, labelbitmap):
        """Returns an 'image' for the preview of the label"""
        # fix size, adding print borders
        labelimage = Image.new('1', (56+labelwidth+56, labelheight))
        labelimage.paste(labelbitmap, (56,0))
        ti = labelimage.convert("PNG")
        print('Image mode is <{}>'.format(ti.mode))
        inverted_image = PIL.ImageOps.invert(ti)
        return inverted_image



    def printLabel(self, labelbitmap):
        # convert the image to the proper matrix for the dymo labeler object
        labelrotated = labelbitmap.transpose(Image.ROTATE_270)
        labelstream = labelrotated.tobytes()
        labelstreamrowlength = labelheight/8 + (1 if labelheight%8 != 0 else 0)
        if len(labelstream)/labelstreamrowlength != labelwidth:
            die('An internal problem was encountered while processing the label '
                'bitmap!')
        labelrows = [labelstream[i:i+labelstreamrowlength] for i in
            range(0, len(labelstream), labelstreamrowlength)]
        labelmatrix = [array.array('B', labelrow).tolist() for labelrow in
            labelrows]

        # optimize the matrix for the dymo label printer
        dottab = 0
        while max(line[0] for line in labelmatrix) == 0:
            labelmatrix = [line[1:] for line in labelmatrix]
            dottab += 1
        for line in labelmatrix:
            while len(line) > 0 and line[-1] == 0:
                del line[-1]
        self.printLabelInternal(labelmatrix, dottab)




    def printLabelInternal(self, lines, dotTab):
        """Print the label described by lines. (HLF)"""

        self.initLabel
        self.tapeColor(0)
        self.dotTab(dotTab)
        for line in lines:
            self.line(line)
        self.skipLines(56)  # advance printed matter past cutter
        self.skipLines(56)  # add symmetric margin
        self.statusRequest()
        response = self.sendCommand()
        print (response)

#######################################################
#######################################################
### End of Object Definition
#######################################################
#######################################################

def die(message=None):
  if message: print(message, file=sys.stderr)
  sys.exit(1)


def pprint(par, fd=sys.stdout):
  rows, columns = struct.unpack('HH', fcntl.ioctl(sys.stderr,
      termios.TIOCGWINSZ, struct.pack('HH', 0, 0)))
  print >> fd, textwrap.fill(par, columns)


def getDeviceFile(classID, vendorID, productID):
    # find file containing the device's major and minor numbers
    searchdir = '/sys/bus/hid/devices'
    pattern = '^%04d:%04X:%04X.[0-9A-F]{4}$' % (classID, vendorID, productID)
    deviceCandidates = os.listdir(searchdir)
    foundpath = None
    for devname in deviceCandidates:
        if re.match(pattern, devname):
            foundpath = os.path.join(searchdir, devname)
            break
    if not foundpath:
        return
    searchdir = os.path.join(foundpath, 'hidraw')
    devname = os.listdir(searchdir)[0]
    foundpath = os.path.join(searchdir, devname)
    filepath = os.path.join(foundpath, 'dev')

    # get the major and minor numbers
    f = open(filepath, 'r')
    devnums = [int(n) for n in f.readline().strip().split(':')]
    f.close()
    devnum = os.makedev(devnums[0], devnums[1])

    # check if a symlink with the major and minor numbers is available
    filepath = '/dev/char/%d:%d' % (devnums[0], devnums[1])
    if os.path.exists(filepath):
        return os.path.realpath(filepath)

    # check if the relevant sysfs path component matches a file name in
    # /dev, that has the proper major and minor numbers
    filepath = os.path.join('/dev', devname)
    if os.stat(filepath).st_rdev == devnum:
        return filepath

    # search for a device file with the proper major and minor numbers
    for dirpath, dirnames, filenames in os.walk('/dev'):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.stat(filepath).st_rdev == devnum:
                return filepath


def access_error(dev):
    pprint('You do not have sufficient access to the device file %s:' % dev,
        sys.stderr)
    subprocess.call(['ls', '-l', dev], stdout=sys.stderr)
    print("", file=sys.stderr)
    pprint('You probably want to add a rule in /etc/udev/rules.d along the '
        'following lines:', sys.stderr)
    print('SUBSYSTEM=="hidraw", ACTION=="add", ATTRS{idVendor}=="{:4x}", ATTRS{idProduct}=="{:4x}", GROUP="plugdev"'.
          format(DEV_VENDOR, DEV_PRODUCT), file=sys.stderr)
    print("", file=sys.stderr)
    pprint('Following that, turn off your device and back on again to '
        'activate the new permissions.', sys.stderr)


''' reading config file, input: 'filename' '''
def read_config(conf_file):
    global FONT_CONFIG
    conf = ConfigParser(FONT_CONFIG)
    if not conf.read(conf_file):
        print('# Config file "%s" not found: writing new config file.\n' %conf_file)
        write_config(conf_file)
    else:
        # reading FONTS section
        if not 'FONTS' in conf.sections():
            die('! config file "%s" not valid. Please change or remove.' %conf_file)
        for key in FONT_CONFIG.keys():
            FONT_CONFIG[key] = conf.get('FONTS',key)
        # more sections later ..


''' writing config file, input: 'filename' '''
def write_config(conf_file):
    config=ConfigParser()
    # adding sections and keys
    config.add_section('FONTS')
    for key in FONT_CONFIG.keys():
        config.set('FONTS', key, FONT_CONFIG[key])
    # writing config file
    with open(conf_file, 'wb') as configfile:
        config.write(configfile)


''' scaling pixel up, input: (x,y),scale-factor '''
def scaling(pix,sc):
  m=[]
  for i in range(sc):
      for j in range(sc):
          m.append( (pix[0]+i,pix[1]+j) )
  return m


''' decoding text parameter depending on system encoding '''
def commandline_arg(bytestring):
  unicode_string = bytestring.decode(sys.getfilesystemencoding())
  return unicode_string

def get_default_dev():
    if not DEV_NODE:
        dev = getDeviceFile(DEV_CLASS, DEV_VENDOR, DEV_PRODUCT)
    else:
        dev = DEV_NODE
    if not dev:
        die("The device '%s' could not be found on this system." % DEV_NAME)
    return dev



def main():
    # get device file name
    if not DEV_NODE:
        dev = getDeviceFile(DEV_CLASS, DEV_VENDOR, DEV_PRODUCT)
    else:
        dev = DEV_NODE
    if not dev:
        die("The device '%s' could not be found on this system." % DEV_NAME)

    # create dymo labeler object
    try:
        lm = DymoLabeler(dev)
    except IOError:
        die(access_error(dev))

    # read config file
    conf_path = os.path.dirname(sys.argv[0])
    read_config(conf_path+'/'+CONFIG_FILE)

    # check for any text specified on the command line
    parser = argparse.ArgumentParser(description=DESCRIPTION+' \n Version: '+VERSION)
    parser.add_argument('text',nargs='+',help='Text Parameter, each parameter gives a new line',type=commandline_arg)
    parser.add_argument('-f',action="count",help='Draw frame around the text, more arguments for thicker frame')
    parser.add_argument('-s',choices=['r','b','i','n'],default='r',help='Set fonts style (regular,bold,italic,narrow)')
    parser.add_argument('-u',nargs='?',help='Set user font, overrides "-s" parameter')
    parser.add_argument('-v',action='store_true',help='Preview label, do not print')
    parser.add_argument('-qr',action='store_true',help='Printing the text parameter as QR-code')
    #parser.add_argument('-t',type=int,choices=[6, 9, 12],default=12,help='Tape size: 6,9,12 mm, default=12mm')
    args = parser.parse_args()
    labeltext = args.text
    # select font style and offset from parameter
    if args.s == 'r':
        FONT_FILENAME = FONT_CONFIG['regular']
    elif args.s == 'b':
        FONT_FILENAME = FONT_CONFIG['bold']
    elif args.s == 'i':
        FONT_FILENAME = FONT_CONFIG['italic']
    elif args.s == 'n':
        FONT_FILENAME = FONT_CONFIG['narrow']
    else:
        FONT_FILENAME = FONT_CONFIG['regular']

    if len(args.u):
        if os.path.isfile(args.u):
            FONT_FILENAME = args.u
        else:
            die("Error: file '%s' not found." % args.u)

    # check if qrcode or text should be printed, use frames only on text
    if args.qr == False:

        if args.f == None:
            fontoffset = 0
        else:
            fontoffset = min(args.f, 3)

        # create an empty label image
        labelheight = lm._MAX_BYTES_PER_LINE * 8
        lineheight = float(labelheight) / len(labeltext)
        fontsize = int(round(lineheight * FONT_SIZERATIO))
        font = ImageFont.truetype(FONT_FILENAME, fontsize)
        labelwidth = max(font.getsize(line)[0] for line in labeltext) + (fontoffset*2)
        labelbitmap = Image.new('1', (labelwidth, labelheight))
        labeldraw = ImageDraw.Draw(labelbitmap)

        # draw frame into empty image
        if len(args.f):
            labeldraw.rectangle(((0,0),(labelwidth-1,labelheight-1)),fill=255)
            labeldraw.rectangle(((fontoffset,fontoffset),(labelwidth-(fontoffset+1),labelheight-(fontoffset+1))),fill=0)

        # write the text into the empty image
        for i, line in enumerate(labeltext):
            lineposition = int(round(i * lineheight))
            labeldraw.text((fontoffset, lineposition), line, font=font, fill=255)
        del labeldraw

    elif USE_QR == False:
        die("Error: %s" % e)
    # create QR object from first string
    else:
        code = QRCode(labeltext[0],error='M')
        qr_text = code.text().split()

        # create an empty label image
        labelheight = e._MAX_BYTES_PER_LINE * 8
        labelwidth = labelheight
        qr_scale = labelheight / len(qr_text)
        qr_offset = (labelheight - len(qr_text)*qr_scale) / 2
        labelbitmap = Image.new('1', (labelwidth, labelheight))
        labeldraw = ImageDraw.Draw(labelbitmap)

        # write the qr-code into the empty image
        for i,line in enumerate(qr_text):
            for j in range(len(line)):
                if line[j]=='1':
                    pix=scaling((j*qr_scale,i*qr_scale+qr_offset),qr_scale)
                    labeldraw.point(pix,255)
        del labeldraw

    # convert the image to the proper matrix for the dymo labeler object
    labelrotated = labelbitmap.transpose(Image.ROTATE_270)
    labelstream = labelrotated.tobytes()
    labelstreamrowlength = labelheight/8 + (1 if labelheight%8 != 0 else 0)
    if len(labelstream)/labelstreamrowlength != labelwidth:
        die('An internal problem was encountered while processing the label '
            'bitmap!')
    labelrows = [labelstream[i:i+labelstreamrowlength] for i in
        range(0, len(labelstream), labelstreamrowlength)]
    labelmatrix = [array.array('B', labelrow).tolist() for labelrow in
        labelrows]

    # optimize the matrix for the dymo label printer
    dottab = 0
    while max(line[0] for line in labelmatrix) == 0:
        labelmatrix = [line[1:] for line in labelmatrix]
        dottab += 1
    for line in labelmatrix:
        while len(line) > 0 and line[-1] == 0:
            del line[-1]

    # print or show the label
    if args.v == True:
        print('Previewing label...')
        # fix size, adding print borders
        labelimage = Image.new('1', (56+labelwidth+56, labelheight))
        labelimage.paste(labelbitmap, (56,0))
        ti = labelimage.convert("PNG")
        print('Image mode is <{}>'.format(ti.mode))
        inverted_image = PIL.ImageOps.invert(ti)
        try:
          with open("preview.jpeg", "w") as file:
            labelimage.save(file, "JPEG");
        except IOError as e:

            print >> sys.stderr, "dymoprint: error generating preview:{}".\
                format(e)
            labelimage.show()
    else:
        print('Printing label..')
        lm.printLabel(labelmatrix, dottab)


if __name__ == '__main__':
    main()


# TODO
# ? support multiple ProductIDs (1001, 1002) -> use usb-modeswitch?
# o put everything in classes that would need to be used by a GUI
# x for more options use command line parser framework
# x allow selection of font with command line options
# o allow font size specification with command line option (points, pixels?)
# x provide an option to show a preview of what the label will look like
# x read and write a .dymoprint file containing user preferences
# o print graphics and barcodes
# x plot frame around label

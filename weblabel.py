#!/usr/bin/env python3

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify

from pprint import pprint, pformat
from shutil import copyfile
import subprocess
import itertools
import sys
import random
import os
import re
import logging

dymoPrefix = "/home/pi/labelprint/"
imgPrefix = "./imgs/"
fnBlank = "preview-none.gif"
fnPreview = "preview.png"
indexFile = "index.html"

pngLen = 0.0
shortLabelDelta = 56.0
ptsPerInch = 72.0

txt2imgProg = dymoPrefix + "txt2img"
printImageProg = dymoPrefix + "imgprint"
defaultFont = "/usr/share/fonts/truetype/" + \
      "msttcorefonts/Comic_Sans_MS_Bold.ttf"


def resetDymo():
    """Reset's the USB interface to the Dymo label printer.
  Found this on the following link:
  http://askubuntu.com/questions/645/how-do-you-reset-a-usb-device-from-the-command-line
  """

    import fcntl
    USBDEVFS_RESET = 21780
    driver = 'Dymo-CoStar Corp'

    try:
        lsusb_out = subprocess.check_output(
            'lsusb | grep -i "%s"' % driver,
            shell=True).decode("utf-8").strip().split()
        bus = lsusb_out[1]
        device = lsusb_out[3][:-1]
        dpath = "/dev/bus/usb/%s/%s" % (bus, device)
        print('\t%s' % dpath)
        f = open(dpath, 'w', os.O_WRONLY)
        fcntl.ioctl(f, USBDEVFS_RESET, 0)
    except Exception as e:
        print("failed to reset device: %s" % repr(e), file=sys.stderr)
        sys.exit(13)


#             template_folder="./",

app = Flask(__name__, static_folder="./", static_url_path="")


def flatten(l):
    for el in l:
        yield el


#hard to be secret in open source... >.>
app.secret_key = 'A0Zr98j/3yX asdfzxcvR~XHH!jmN]LWX/,?RT'

formText = "Up to 3 lines max"


def genPreview(lines, left, right, shortLabel, printIt=False):
    global pngLen
    # DBG:
    log.info('*****\n****\n**** Working dir is %s' % os.getcwd())
    # print("***  Generating preview with %s\n"%repr(lines))
    # print("*** Preview and the text is <{}>".format(
    #     formText))
    # print("Label Left = {}, Label Right = {}".format(
    #     left, right))
    # print("Len of lines is %d"%len(lines))
    for i in range(0, len(lines)):
        if (not len(lines[i])) or lines[i].isspace():
            lines[i] = ""
        # for i in lines:
        #   print("%s"%repr(i))
        if not len(lines):
            return "Empty input data"
    if len(lines) > 3:
        return "Too many lines (>3) = %d" % len(lines)
    # Specify left, right or no alignment
    if left:
        alignArr = ['-a', 'l']
    elif right:
        alignArr = ['-a', 'r']
    else:
        alignArr = []

    # For safety's sake, reset the USB on the label printer
    resetDymo()

    #
    # Now, try to call the txt2img program.
    #
    # If things go well, it will ~create a file called "imgs/preview.png"
    # which has the preview image.
    #
    try:
        subProcArr = [
            txt2imgProg,
            '-f',
            defaultFont,
            '-o',
            imgPrefix + fnPreview,
            alignArr,
            lines,
        ]
        #
        # Flattens the list subProcArr
        # Snarfed from Reedy's comment on
        # http://stackoverflow.com/questions/
        #    5286541/how-can-i-flatten-lists-without-splitting-strings
        #
        subProcArr = list(
            itertools.chain.from_iterable(
                itertools.repeat(x, 1) if isinstance(x, str) else x
                for x in subProcArr))
        log.info("***\n*** Calling program %s\n***" %
                 repr(subProcArr))  #DBG#
        # log.error("This is an error log %s"%repr(subProcArr))
        subprocess.check_output(subProcArr)
    except subprocess.CalledProcessError as e:
        return "error running txt2img: %s" % (repr(e))

    pngInfo = subprocess.check_output(
        ['/usr/bin/file', imgPrefix + fnPreview],
        shell=False).decode("utf-8")
    # preview.png: PNG image data, 606 x 64, 8-bit/color RGB, non-interlaced
    match = re.search(r'PNG image data, ([0-9]+) x [0-9]+', pngInfo)
    tmpLen = int(match.group(1))
    if not match:
        print(
            '{}: error getting png info:{}:{}'.format(
                sys.argv[0], imgPrefix + fnPreview, repr(pngInfo)),
            file=sys.stderr)
        sys.exit(23)
    pngLen = float(tmpLen +
                   (0 if shortLabel else shortLabelDelta)) / ptsPerInch

    if not printIt:
        return None

    # Reset the USB setting
    import time
    time.sleep(1)
    #
    # Now, print the file
    #

    shortArr = []
    if shortLabel:
        shortArr = ['-s']
    try:
        subProcArr = [ "/usr/bin/nice", "-20", printImageProg, \
            shortArr, imgPrefix+fnPreview ]
        subProcArr = list(
            itertools.chain.from_iterable(
                itertools.repeat(x, 1) if isinstance(x, str) else x
                for x in subProcArr))
        log.info("***\n*** Calling program %s\n***" %
                 repr(subProcArr))  #DBG#
        subprocess.check_output(subProcArr)
    except subprocess.CalledProcessError as e:
        return "error running imgprint with %s: %s" % (
            imgPrefix + fnPreview, repr(e))


@app.route('/')
@app.route('/index')
def my_form():
    global formText, pngLen
    #
    # Copy the blank image file to the preview image file
    #
    if not len(formText):
        shutil.copyfile(imgPrefix + fnBlank, imgPrefix + fnPreview)

    # Parse the LeftLab and RightLab to see if they exist (needed
    # for both Preview and Print)
    checkboxAlignRight = False
    checkboxAlignLeft = False
    shortLabel = False

    if 'checkboxAlignRight' in request.args:
        checkboxAlignRight = True

    if 'checkboxAlignLeft' in request.args:
        checkboxAlignLeft = True

    if 'Label-Short' in request.args:
        shortLabel = True

    labelText = request.args.get('labelText')
    # print('DBG: URL line is %s'%repr(labelText))
    if labelText:
        lines = [x.rstrip() for x in labelText.split('\n')]
    else:
        lines = []

    # print("*********************************************")
    # print("*********************************************")
    # print("*********************************************")
    # print("DBG: labelText = %s\nlines = %s"%(repr(labelText), repr(lines)))

    #
    # Preview
    #
    if 'previewBtn' in request.args:
        rv = genPreview(lines, checkboxAlignLeft, checkboxAlignRight,
                        shortLabel)
        if rv:
            return render_template(
                indexFile,
                warnText=rv,
                imgFile=fnBlank,
                tics=str(random.random()),
                deleteCookies="false",
                desc='Len = {:.1f} in.'.format(pngLen),
                displayText="")
        else:
            return render_template(
                indexFile,
                warnText="",
                imgFile=fnPreview,
                tics=str(random.random()),
                deleteCookies="false",
                desc='Len = {:.1f} in.'.format(pngLen),
                displayText=request.args.get('labelText'))

    #
    # PRINT
    #
    elif 'printBtn' in request.args:
        rv = genPreview(
            lines,
            checkboxAlignLeft,
            checkboxAlignRight,
            shortLabel,
            printIt=True)
        if rv:
            return render_template(
                indexFile,
                warnText=rv,
                imgFile=fnBlank,
                tics=str(random.random()),
                desc='Printed',
                deleteCookies="false",
                displayText="")
        else:
            return render_template(
                indexFile,
                warnText="",
                imgFile=fnPreview,
                tics=str(random.random()),
                desc='Printed',
                deleteCookies="false",
                displayText=request.args.get('labelText'))

        # Successful completion of generating preview, now print it
        # by calling the "imgprint" function.
        print("Generated preview, stubbed PRINT function")  #DBG#
        return rv

    #
    # INITIAL SCREEN RENDERING
    #
    elif not len(request.args):
        print('indexFile is %s' % repr(indexFile))
        session.clear()
        # print("**** It's the first screen draw, no args")
        formText = "Up to 3 lines max"
        rv = render_template(
            indexFile,
            displayText=formText,
            warnText="",
            imgFile=fnBlank,
            deleteCookies="true",
            tics=str(random.random()))

        app.secret_key = os.urandom(32)
        resp = rv
        return resp

    #
    # *** ERROR ***
    #
    else:
        print("****\n**** ERROR invalid args:", pformat(request.args))
        return render_template(
            indexFile,
            displayText=formText,
            warnText="Invalid args",
            tics=str(random.random()))


if __name__ == "__main__":
    wlog = logging.getLogger('werkzeug')
    wlog.setLevel(logging.INFO)

    # Write the name of the label printer into
    # ./templates/LABELHOST.txt.  Lookup the entries
    # in ./HOSTMAP.txt
    # Store this into ----> 'pageName'
    pageName = "NOTFOUND"
    hostname = os.uname().nodename
    try:
        with open("HOSTMAP.txt", "r") as file:
            for line in file:
                (regex, label) = line.split(None, 1)
                match = re.match(regex, hostname)
                if match:
                    pageName = label.strip()
                    break
            if pageName == "NOTFOUND":
                print(
                    '%s:labeller name not found in HOSTMAP.txt, defaulting to %s'
                    % (sys.argv[0], 'Labeller'),
                    file=sys.stderr)
                pageName = 'Labeller'
    except IOError:
        print(
            '%s: Error opening HOSTMAP.txt, defaulting to %s' %
            (sys.argv[0], 'Labeller'),
            file=sys.stderr)
        pageName = 'Labeller'
    # Now, write out the $pageName to the ./templates/LABELHOST.txt file
    try:
        with open('templates/LABELHOST.txt', "w") as file:
            file.write(pageName + '\n')
    except IOError as e:
        print(
            '{}: Fatal error writing "templates/LABELHOST.txt": {}'.
            format(sys.argv[0], repr(e)),
            file=sys.stderr)
        sys.exit(5)
    print('... Page title is %s' % pageName)

    conh = logging.StreamHandler()
    conh.setLevel(logging.INFO)

    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    log.addHandler(conh)

    log.info('My execpath is %s' % repr(os.get_exec_path()))
    log.info('HTML Index file is %s' % repr(indexFile))

    log.info("Info output")
    log.debug("debug output")
    log.error("error output")

    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run("0.0.0.0", port=80, debug=True)

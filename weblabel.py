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
import logging

dymoPrefix="/home/pi/labelprint/"
imgPrefix="./imgs/"
fnBlank = "preview-none.gif"
fnPreview = "preview.png"

txt2imgProg = dymoPrefix + "txt2img"
printImageProg = dymoPrefix + "imgprint"
defaultFont = "/usr/share/fonts/truetype/" + \
      "msttcorefonts/Comic_Sans_MS_Bold.ttf"


app = Flask(__name__,
            template_folder="./",
            static_folder="./",
            static_url_path="")

def flatten(l):
  for el in l:
    yield el


#hard to be secret in open source... >.>
app.secret_key = 'A0Zr98j/3yX asdfzxcvR~XHH!jmN]LWX/,?RT'

formText="Up to 3 lines max"

def genPreview(lines, left, right, shortLabel, printIt = False):
  # print("***  Generating preview with %s\n"%repr(lines))
  # print("*** Preview and the text is <{}>".format(
  #     formText))
  # print("Label Left = {}, Label Right = {}".format(
  #     left, right))
  # print("Len of lines is %d"%len(lines))
  for i in range(0,len(lines)):
    if (not len(lines[i])) or lines[i].isspace():
      lines[i]="";
  # for i in lines:
  #   print("%s"%repr(i))
  if not len(lines):
    return "Empty input data"
  if len(lines) > 3:
    return "Too many lines (>3) = %d"%len(lines)
  # Specify left, right or no alignment
  if left:
    alignArr = ['-a', 'l']
  elif right:
    alignArr = ['-a', 'r']
  else:
    alignArr = []
  #
  # Now, try to call the txt2img program.
  #
  # If things go well, it will create a file called "imgs/preview.png"
  # which has the preview image.
  #
  try:
    subProcArr = [ txt2imgProg, '-f', defaultFont, '-o', imgPrefix+fnPreview,
        alignArr,
        lines,
        ]
    #
    # Flattens the list subProcArr
    # Snarfed from Reedy's comment on
    # http://stackoverflow.com/questions/
    #    5286541/how-can-i-flatten-lists-without-splitting-strings
    #
    subProcArr = list(itertools.chain.from_iterable(itertools.repeat(x,1)
                      if isinstance(x,str) else x for x in subProcArr))
    log.info("***\n*** Calling program %s\n***"%repr(subProcArr))   #DBG#
    # log.error("This is an error log %s"%repr(subProcArr))
    subprocess.check_output(subProcArr)
  except subprocess.CalledProcessError as e:
    return "error running txt2img: %s"%(repr(e))

  if not printIt:
    return False
  #
  # Now, print the file
  #
  shortArr = []
  if shortLabel:
    shortArr = ['-s']
  try:
    subProcArr = [ printImageProg, shortArr, imgPrefix+fnPreview ]
    subProcArr = list(itertools.chain.from_iterable(itertools.repeat(x,1)
                      if isinstance(x,str) else x for x in subProcArr))
    log.info("***\n*** Calling program %s\n***"%repr(subProcArr))   #DBG#
    subprocess.check_output(subProcArr)
  except subprocess.CalledProcessError as e:
    return "error running imgprint with %s: %s"%(imgPrefix+fnPreview, repr(e))


@app.route('/')
@app.route('/index')
def my_form():
  global formText
  #DBG: print("Redrawing form")
  #
  # Copy the blank image file to the preview image file
  #
  if not len(formText):
    shutil.copyfile(imgPrefix+fnBlank, imgPrefix+fnPreview)

  # Parse the LeftLab and RightLab to see if they exist (needed
  # for both Preview and Print)
  wireLabelRight = False
  wireLabelLeft = False
  shortLabel = False

  if 'wireCB-Right' in request.args:
    wireLabelRight = True

  if 'wireCB-Left' in request.args:
    wireLabelLeft = True

  if 'Label-Short' in request.args:
    shortLabel = True

  labelText = request.args.get('labelText')
  # print('DBG: URL line is %s'%repr(labelText))
  if labelText:
    lines = [ x.rstrip() for x in labelText.split('\n')]
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
    rv = genPreview(lines, wireLabelLeft, wireLabelRight, shortLabel)
    if rv:
      return render_template("./index.html", warnText = rv, imgFile=fnBlank,
                             tics=str(random.random()),
                             deleteCookies="false",
                             displayText="")
    else:
      return render_template("./index.html", warnText = "", imgFile=fnPreview,
                              tics=str(random.random()),
                              deleteCookies="false",
                              displayText = request.args.get('labelText'))

  #
  # PRINT
  #
  elif 'printBtn' in request.args:
    rv = genPreview(lines, wireLabelLeft, wireLabelRight,
                    shortLabel, printIt = True)
    if rv:
      return render_template("./index.html", warnText = rv, imgFile=fnBlank,
                             tics=str(random.random()),
                             deleteCookies="false",
                             displayText="")
    else:
      return render_template("./index.html", warnText = "", imgFile=fnPreview,
                              tics=str(random.random()),
                              deleteCookies="false",
                              displayText = request.args.get('labelText'))


    # Successful completion of generating preview, now print it
    # by calling the "imgprint" function.
    print("Generated preview, stubbed PRINT function")  #DBG#
    return rv

  #
  # INITIAL SCREEN RENDERING
  #
  elif not len(request.args):
    session.clear()
    # print("**** It's the first screen draw, no args")
    formText="Up to 3 lines max"
    rv = render_template("./index.html", displayText = formText,
                           warnText = "", imgFile = fnBlank,
                           deleteCookies="true",
                           tics = str(random.random()))

    app.secret_key = os.urandom(32)
    resp = rv
    return resp


  #
  # *** ERROR ***
  #
  else:
    print("****\n**** ERROR invalid args:", pformat(request.args))
    return render_template("./index.html", displayText = formText,
                           warnText = "Invalid args",
                           tics = str(random.random()))


if __name__ == "__main__":
  wlog = logging.getLogger('werkzeug')
  wlog.setLevel(logging.INFO)

  conh = logging.StreamHandler()
  conh.setLevel(logging.INFO)


  log = logging.getLogger('')
  log.setLevel(logging.INFO)
  log.addHandler(conh)

  log.info("Info output")
  log.debug("debug output")
  log.error("error output")

  app.config['DEBUG'] = False
  app.config['TEMPLATES_AUTO_RELOAD'] = False
  app.run("0.0.0.0", port=5000, debug=False)

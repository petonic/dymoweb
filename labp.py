#!/usr/bin/env python3

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify

from pprint import pprint, pformat


app = Flask(__name__,
            template_folder="./",
            static_folder="./",
            static_url_path="")

#hard to be secret in open source... >.>
app.secret_key = 'A0Zr98j/3yX asdfzxcvR~XHH!jmN]LWX/,?RT'


@app.route('/')
@app.route('/index')
def my_form():
  print("Redrawing form")
  # Parse the LeftLab and RightLab to see if they exist (needed
  # for both Preview and Print)
  wireLabelRight = 0
  wireLabelLeft = 0
  if 'wireCB-Right' in request.args:
    wireLabelRight = 1

  if 'wireCB-Left' in request.args:
    wireLabelLeft = 1


  if 'previewBtn' in request.args:
    #
    print("**** Preview and the text is <{}>".format(
        request.args.get('labelText')))
    print("Label Left = {}, Label Right = {}".format(
        wireLabelLeft, wireLabelRight))
    print(pformat(request.args))

  elif 'printBtn' in request.args:
    #
    print("**** Printand the text is <{}>".format(
        request.args.get('labelText')))
    print("Label Left = {}, Label Right = {}".format(
        wireLabelLeft, wireLabelRight))
    print(pformat(request.args))


  elif not len(request.args):
    print("**** First screen draw, no args")

  else:
    print("****\n**** ERROR invalid args:", pformat(request.args))


  rv =render_template("./index.html")

  return rv



if __name__ == "__main__":

  app.config['DEBUG'] = True
  app.config['TEMPLATES_AUTO_RELOAD'] = True
  app.run("0.0.0.0", port=5000, debug=True)

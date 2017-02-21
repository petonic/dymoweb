#!/usr/bin/env python3

import dymoprint
dp = dymoprint

def main():
  print("At the start of MAIN")
  defDev = dp.get_default_dev()

  lm = dymoprint.DymoLabeler(defDev)
  tempLabel = lm.create_label("Foo")
  preview = ln.previewLabel(tempLabel)
  try:
    with open("preview.jpeg", "w") as file:
      labelimage.save(file, "JPEG");
  except IOError as e:

      print >> sys.stderr, "dymoprint: error generating preview:{}".\
          format(e)
      labelimage.show()
  print("Saved preview to 'preview.jpg'")





if __name__ == '__main__':
  from pdb import set_trace as bp; bp()
  main()

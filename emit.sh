set -eu

target="a.html"

python3 main.py

rm -f $target

echo """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta NAME="viewport" content="width=device-width, initial-scale=1" />
    <style></style>
  </head>
  <body>""" >> $target

marked --gfm -i out/meshi.md >> $target

echo """
  </body>
</html>""" >> $target


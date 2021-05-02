set -eu

target="a.html"

python3 main.py

mkdir -p out

rm -fr out/img

rm -f $target

echo """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta NAME="viewport" content="width=device-width, initial-scale=1" />
    <title>はるかめしにっき</title>
    <style></style>
  </head>
  <body>""" >> $target

marked --gfm -i out/meshi.md >> $target

cp -r img out
cp $target out

echo """
  </body>
</html>""" >> $target


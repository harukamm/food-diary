set -eu

meshi_html="a.html"
kaimono_html="b.html"

function output_meshi() {
  echo """<!DOCTYPE html>
  <html>
    <head>
      <meta charset="UTF-8" />
      <meta NAME="viewport" content='width=device-width, initial-scale=1' />
      <title>はるかめしにっき</title>
      <style></style>
    </head>
    <body>""" >> $meshi_html
  
  marked --gfm -i out/meshi.md >> $meshi_html
  
  echo """
    </body>
  </html>""" >> $meshi_html
}

function output_kaimono() {
  echo """<!DOCTYPE html>
  <html>
    <head>
      <meta charset='UTF-8' />
      <meta NAME='viewport' content='width=device-width, initial-scale=1' />
      <title>買い物リスト</title>
      <script>
      function get() {
        return JSON.parse(localStorage.getItem('formValues')) || {};
      }
      function store(formValues) {
        localStorage.setItem('formValues', JSON.stringify(formValues));
      }
      function storeVal(id, val) {
        const vals = get();
        if (val) {
          vals[id] = true;
        } else {
          delete vals[id];
        }
        store(vals);
      }
      function restoreVal() {
        const vals = get();
        Object.keys(vals).map(key => {
          const val = vals[key];
          if (!val) return;
          const node = document.querySelector('input[name=' + key + ']');
          node.checked = true;
        });
      }
      function clearVals() {
        store({});
        const nodes = document.querySelectorAll('input[type=checkbox]');
        for (var i = 0; i < nodes.length; i++) {
          const node = nodes[i];
          node.checked = false;
        }
      }
      function addListeners() {
        // to clear buttons
        const buttons = document.querySelectorAll('.clear-button');
        for (var i = 0; i < buttons.length; i++) {
          const button = buttons[i];
          button.addEventListener('click', function() {
            clearVals();
          });
        }

        // to checkboxes
        const nodes = document.querySelectorAll('input[type=checkbox]');
        for (var i = 0; i < nodes.length; i++) {
          const node = nodes[i];
          const name = node.name;
          node.addEventListener('change', function() {
            storeVal(name, this.checked);
          });
        }
      }
      window.addEventListener('load', (event) => {
        restoreVal();
        addListeners();
      });
      </script>
      <style></style>
    </head>
    <body>
    <input type='button' value='クリア' class='clear-button' />
    """ >> $kaimono_html
  
  marked --gfm -i out/kaimono.md >> $kaimono_html
  
  echo """
    <input type='button' value='クリア' class='clear-button' />
    </body>
  </html>""" >> $kaimono_html
}

python3 main.py meshi kaimono

mkdir -p out
rm -fr out/img
rm -f $meshi_html $kaimono_html

output_meshi
output_kaimono

cp -r img out
cp $meshi_html out
cp $kaimono_html out

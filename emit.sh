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
      <style>
        table { border-collapse: collapse; }
        table, td, th {
          border: 1px solid black;
        }
        td, th {
          padding: 5px;
        }
        th {
          background-color: #eee;
        }
      </style>
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
          vals[id] = val;
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
          if (key == 'free-memo') {
            const node = document.getElementById('free-memo');
            if (node) node.textContent = val;
          } else {
            const node = document.querySelector('input[name=' + key + ']');
            if (node) node.checked = true;
          }
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
      function syncCheckedItems() {
        const nodes = document.querySelectorAll('input[type=checkbox]');
        const names = [];
        for (var i = 0; i < nodes.length; i++) {
          const node = nodes[i];
          if (!node.checked) continue;

          var elem = node.nextSibling;
          var title = null;
          while (elem) {
            console.log(elem);
            if (elem.className == 'title') {
              break;
            }
            const nested = elem.querySelector('.title');
            if (nested) {
              elem = nested;
              break;
            }
            elem = elem.nextSibling;
          }
          if (!elem) continue;
          const name = elem.textContent.trim();
          names.push(name);
        }
        document.getElementById('names').textContent = names.join(', ');
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

        // to free textarea
        const node = document.getElementById('free-memo');
        node.addEventListener('input', function(e) {
          storeVal('free-memo', e.target.value);
        });
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
    <br />
    <br />
    <textarea style='width:100%;' id='free-memo'></textarea>
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

import os
from flask import Flask, request
import uuid
import base64
from api import process_image
import sqlite3

app = Flask(__name__)


LOCAL_IMG_DIR = '../client/inputfolder'
DATABASE_FILE = './images.db'
IMAGES = []
ALL_LABELS = []


class ImageObject(object):
    def __init__(self, id, base64_img, tags):
        self.id = id
        self.base64_img = base64_img
        self.tags = tags

    def __str__(self):
        return "id:{}\ntags:{}\n---".format(self.id, self.tags)


def init_imageDB():
    print('Creating database...')
    global IMAGES
    global ALL_LABELS

    # Init image objects and tags
    for img in os.listdir(LOCAL_IMG_DIR):
        img = os.path.join(LOCAL_IMG_DIR, img)
        # res += "<p>{}</p>".format(img)
        ID = uuid.uuid5(uuid.NAMESPACE_OID, img)
        # Encode image into base64 string
        tags = []
        base64_img = ""
        with open(img, 'rb') as image_file:
            base64_img = base64.b64encode(image_file.read()).decode('utf-8')
            for obj in process_image(base64_img):
                tags.append(obj['label'])
                # print(tags)
            ALL_LABELS += tags

        IMAGES.append(ImageObject(str(ID), base64_img, tags))

    ALL_LABELS = list(set(ALL_LABELS))
    label_cols = ", ".join([label + " INT" for label in ALL_LABELS])
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    create_table = 'CREATE TABLE images (id TEXT PRIMARY KEY, base64_img TEXT, {})'.format(
        label_cols)
    cur.execute(create_table)

    for img_obj in IMAGES:
        tags = [0] * len(ALL_LABELS)
        for t in img_obj.tags:
            tags[ALL_LABELS.index(t)] = 1
        row = ["'{}'".format(img_obj.id), "'{}'".format(img_obj.base64_img)] + \
            [str(tag) for tag in tags]
        insert = '''INSERT INTO images VALUES({});'''.format(", ".join(row))
        cur.execute(insert)
        conn.commit()

    conn.close()


def load_images(filter_string=""):
    global IMAGES

    res = """
        <style>
        # container {

            text-align: justify;
            -ms-text-justify: distribute-all-lines;
            text-justify: distribute-all-lines;

            /* just for demo */

        }

        .box {
            width: 150px;
            height: 125px;
            background:#ccc;
            border-radius: 10px;
            vertical-align: top;
            display: inline-block;
            *display: inline;
            margin:10px;
            zoom: 1
        }
        .stretch {
            width: 100%;
            display: inline-block;
            font-size: 0;
            line-height: 0
        }

        /* Add a black background color to the top navigation bar */
        .topnav {
          overflow: hidden;
          background-color: #e9e9e9;
          padding: 3px;
        }

        /* Style the links inside the navigation bar */
        .topnav a {
          float: left;
          display: block;
          color: black;
          text-align: center;
          padding: 14px 16px;
          text-decoration: none;
          font-size: 17px;
        }

        /* Change the color of links on hover */
        .topnav a:hover {
          background-color: #ddd;
          color: black;
        }

        /* Style the "active" element to highlight the current page */
        .topnav a.active {
          background-color: #2196F3;
          color: white;
        }

        /* Style the search box inside the navigation bar */
        .topnav input[type=text] {
          width: 80%;
          padding: 6px;
          border: none;
          border-radius: 6px;
          margin-top: 8px;
          margin-right: 16px;
          font-size: 17px;
        }

        /* When the screen is less than 600px wide, stack the links and the search field vertically instead of horizontally */
        @media screen and (max-width: 600px) {
          .topnav a, .topnav input[type=text] {
            float: none;
            display: block;
            text-align: left;
            width: 100%;
            margin: 0;
            padding: 14px;
          }
          .topnav input[type=text] {
            border: 1px solid #ccc;
          }
        }
        </style>

        <form method='post'>

        <div class="topnav">
          <input type="text" name="query" placeholder="Search..">
            <input type="submit" value="Submit">

        </div>

        </form>

       <div id="container">
        @
    <span class="stretch"></span>
</div>
    """

    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    query = ""
    if filter_string == "":
        query = "SELECT * FROM images"
    else:
        query = "SELECT * FROM images WHERE({} = 1)".format(filter_string)

    cur.execute(query)
    images = cur.fetchall()
    conn.close()

    image_grid_html = ""
    for img_obj in images:
        image_grid_html += "<div class='box'> <img style='width:inherit; height: inherit' src ='data:image/png;base64,{}' alt='image' / > </div>".format(
            img_obj[1])

    res = res.replace('@', image_grid_html)

    return res


@ app.route('/', methods=['GET', 'POST'])
def home():
    if not os.path.exists(DATABASE_FILE):
        init_imageDB()
    if request.method == "POST":
        return load_images(filter_string=request.form['query'])
    return load_images()


app.run(debug=True)

import os
import cv2
import json
import logging

import numpy as np

from datetime import datetime
from flask import Blueprint, Response, render_template, send_from_directory, request, redirect, url_for
from flask import flash
from flask_user import login_required, current_user

from .helpers.generic import Timer
from .helpers.persistent_obj import PersistentBuffer
from .helpers.ml_object import CardDetector

from .models import User, Game
from . import db

from base64 import encodebytes

permanent_storage_path = '/mnt/mounted_volume/permanentstorage/'
base_ouput_img_dir = os.path.join(permanent_storage_path, "processed_images")
os.makedirs(base_ouput_img_dir, exist_ok=True)

main = Blueprint('main', __name__)

persist_buff = PersistentBuffer()
persist_buff.create_black_buffer()

models_dir_path = "/app/tf_models"
card_detector_ckpt_dir = os.getenv("CARD_DETECTOR_MODEL")
src_model_path = os.path.join(models_dir_path, "card_full_model", card_detector_ckpt_dir)
card_detector = CardDetector(src_model_path, score_threshold=0.5)
card_detector.load_model()
card_detector.initialise_model()

logging.info("Server is ready to detect.")

def get_largest_game_step(input_game_name):
    ##### if no elements are found, an empty list is returned
    current_game_all_steps = Game.query.filter_by(name = input_game_name).all()

    if len(current_game_all_steps) > 0:
        return sorted([ggg.step for ggg in current_game_all_steps])[-1]
    else:
        return -1
def sanify_string_for_path(input_string):
    return input_string.translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+ "})
def game_exists(input_game_name, current_user_email):
    all_games = Game.query.filter_by(name = input_game_name, step = 0, requested_for_email = current_user_email).all()
    # if current_user_email:
    #     all_games = [ggg for ggg in all_games if (current_user_email in [uuu.email for uuu in ggg.requested_for] )]
    return len(all_games) > 0

##### Static routes #####
@main.route('/webrtc/<path:path>')
@login_required
def send_webrtc(path):
    return send_from_directory( os.path.join('/app/server_project/static_files/', 'webrtc'), path)
@main.route('/css/<path:path>')
@login_required
def send_css(path):
    return send_from_directory( os.path.join('/app/server_project/static_files/', 'css'), path)
@main.route('/bulma-0.9.1/<path:path>')
def send_bulma(path):
    return send_from_directory( os.path.join('/app/server_project/static_files/', 'bulma-0.9.1'), path)
##### End #####

##### Main routes #####
@main.route('/')
def index():
    return render_template('index.html')
@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)
##### End #####

##### Route decorators #####
@main.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['Cache-Control'] = ' no-store, max-age=0, must-revalidate'
    return response
##### End #####

##### Game routes #####
@main.route('/startgame')
@login_required
def startgame():
    if current_user.current_game:
        game_name = current_user.current_game
        game_step = get_largest_game_step(game_name) + 1

        end_game = Game(
            name=game_name,
            step=game_step,
            requested_for_email=current_user.email,
            step_at=datetime.utcnow(),
            phase='end')

        current_user.current_game = None

        db.session.add(end_game)
        db.session.commit()

        msg = "Game {0} was ended.".format(game_name)
        logging.info(msg)

    return render_template('startgame.html')
@main.route('/game')
@login_required
def game():
    return render_template('capture_tf.html', gameName=current_user.current_game)
@main.route('/game', methods=["POST"])
@login_required
def game_post():
    game_name = "N/A"
    if current_user.current_game is None:
        game_name = request.form.get('gameName')

        if game_exists(game_name, current_user.email):
            flash('Game \"{0}\" already exists.'.format(game_name))
            return redirect(url_for('main.startgame'))

        game_rule = request.form.get('gameType')

        new_game = Game(
            name=game_name,
            step=0,
            requested_for_email=current_user.email,
            step_at=datetime.utcnow(),
            rule=game_rule,
            phase='start')

        new_game.requested_for.append(current_user)

        current_user.current_game = game_name

        db.session.add(new_game)
        db.session.commit()

        msg = "Game {0} is started.".format(game_name)
        logging.info(msg)

    return render_template('capture_tf.html', gameName=game_name)
@main.route("/updategame", methods=["POST"])
@login_required
def update_game():
    cards_info = request.form.get("cardsInfo")
    game_player = request.form.get('gamePlayer')

    game_step = -2
    if current_user.current_game:
        game_name = current_user.current_game
        game_step = get_largest_game_step(game_name) + 1

        is_img_saved = False
        if len(cards_info) > 0:
            box_detections_string = request.form.get('detections_with_boxes')
            box_detections = json.loads(box_detections_string)

            input_prc_img = request.files['img'].read()
            prc_img = cv2.imdecode(np.fromstring(input_prc_img, np.uint8), 1)

            sanified_email = sanify_string_for_path(current_user.email)
            sanified_game_name = sanify_string_for_path(game_name)

            base_save_path = os.path.join(base_ouput_img_dir, sanified_email, sanified_game_name)
            base_file_name = "img_step_{0:03d}".format(game_step)
            
            prc_img_path = os.path.join(base_save_path, "raw", base_file_name + ".jpg")
            os.makedirs(os.path.dirname(prc_img_path), exist_ok=True)
            cv2.imwrite(prc_img_path, prc_img)

            annotation_path = os.path.join(base_save_path, "annotations", base_file_name + ".json")
            os.makedirs(os.path.dirname(annotation_path), exist_ok=True)

            with open(annotation_path, "w") as f:
                json.dump(box_detections, f)

            is_img_saved = True
            logging.info("Processed image saved: {0}".format(prc_img_path))

        step_game = Game(
            name=game_name,
            step=game_step,
            requested_for_email=current_user.email,
            step_at=datetime.utcnow(),
            phase='running',
            player=game_player,
            detected_cards=cards_info,
            image_is_saved=is_img_saved)

        db.session.add(step_game)
        db.session.commit()

        msg = "Game {0} was updated to step {1}.".format(game_name, game_step)
        logging.info(msg)

        resp = {}
        resp["status"] = "success"
        resp["gameStep"] = game_step + 1

        return resp
    else:
        msg = "No game is currently set for user {0}.".format(current_user.name)
        logging.info(msg)
        return redirect(url_for('startgame'))
##### End #####

##### Image processing routes #####
@main.route("/img", methods=["POST"])
@login_required
def img():
    timer = Timer()

    req_video = request.files['video'].read()
    original_img = cv2.imdecode(np.fromstring(req_video, np.uint8), 1)

    im_height, im_width, im_channels = original_img.shape
    msg = "Received image with shape {0}".format(original_img.shape)
    logging.info(msg)

    detections, predictions_dict, shapes = card_detector.detect_image(original_img)

    logging.info("Image processed in {0}".format(timer.str_timedelta()))

    resize_img = False
    if resize_img:
        img = cv2.resize(img, (480, 300))

    prc_img = original_img.copy()

    card_detector.draw_boxes_on_img(
        detections['detection_boxes'][0].numpy(),
        detections['detection_classes'][0].numpy(),
        detections['detection_scores'][0].numpy(),
        prc_img)

    rel_detections = card_detector.stringify_detections(detections)
    rel_detections_with_boxes = card_detector.stringify_detections_with_boxes(detections)

    resp_dict = {}
    resp_dict["found_cards"] = rel_detections
    resp_dict["detections_with_boxes"] = rel_detections_with_boxes

    persist_buff.load_img_to_buffer(original_img)
    encoded_img = encodebytes(persist_buff.buffer).decode('ascii')
    resp_dict["original_img"] = "data:image/jpeg;base64, {0}".format(encoded_img)

    persist_buff.load_img_to_buffer(prc_img)
    encoded_img = encodebytes(persist_buff.buffer).decode('ascii')
    resp_dict["prc_img"] = "data:image/jpeg;base64, {0}".format(encoded_img)

    return resp_dict
@main.route('/feed')
@login_required
def feed():
    img_content = persist_buff.buffer

    msg = b'--frame\r\n'+ b'Content-Type: image/jpeg\r\n\r\n' + img_content + b'\r\n'
    return Response(msg, mimetype='multipart/x-mixed-replace; boundary=frame')
##### End #####

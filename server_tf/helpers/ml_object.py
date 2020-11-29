import os
import cv2
import six
import logging
import collections

import tensorflow as tf

from datetime import datetime

from object_detection.utils import config_util, label_map_util
from object_detection.builders import model_builder

from .generic import Timer

import matplotlib.pyplot as plt
import numpy as np
from six import BytesIO
from PIL import Image
from object_detection.utils import visualization_utils as viz_utils

from colorsys import hsv_to_rgb

class CardDetector:

    def __init__(self, model_ckp_path, score_threshold = 0.5):
        self.model_ckp_path = model_ckp_path

        self.label_id_offset = 1
        self.score_threshold = score_threshold

    ##### Main Functions #####
    def load_model(self):
        pipeline_config = os.path.join(self.model_ckp_path, "pipeline.config")
        model_dir = os.path.join(self.model_ckp_path, "checkpoint")
        label_map_path = os.path.join(self.model_ckp_path, "label_map.pbtxt")

        configs = config_util.get_configs_from_pipeline_file(pipeline_config)
        model_config = configs['model']
        detection_model = model_builder.build(model_config=model_config, is_training=False)

        ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
        ckpt.restore(os.path.join(model_dir, 'ckpt-0')).expect_partial()

        msg = "Model was restored: {0}".format(model_dir)
        logging.info(msg)

        self.detect_fn = self.get_model_detection_function(detection_model)

        label_map = label_map_util.load_labelmap(label_map_path)
        categories = label_map_util.convert_label_map_to_categories(
            label_map,
            max_num_classes=label_map_util.get_max_label_map_index(label_map),
            use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)
        label_map_dict = label_map_util.get_label_map_dict(label_map, use_display_name=True)

        msg = "Label map was loaded: {0}".format(label_map_path)
        logging.info(msg)

        self.assign_color_to_classes()
    def detect_image(self, input_image_np):
        input_tensor = tf.convert_to_tensor(
            np.expand_dims(input_image_np, 0), dtype=tf.float32)
        return self.detect_fn(input_tensor)
    def detect_test_images(self, test_images_path):
        image_dir = os.path.join(test_images_path, "src")
        dst_dir = os.path.join(test_images_path, "dst")

        for fff in os.listdir(image_dir):
            if fff.endswith(".jpg"):
                image_path = os.path.join(image_dir, fff)
                dst_path = os.path.join(dst_dir, fff)
                image_np = self.load_image_into_numpy_array(image_path)

                detections, predictions_dict, shapes = self.detect_image(image_np)

                image_np_with_detections = image_np.copy()

                viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    detections['detection_boxes'][0].numpy(),
                    (detections['detection_classes'][0].numpy() + self.label_id_offset).astype(int),
                    detections['detection_scores'][0].numpy(),
                    self.category_index,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=10,
                    min_score_thresh=.30,
                    agnostic_mode=False)

                plt.figure(figsize=(12,16))
                plt.imsave(dst_path, image_np_with_detections)
    def initialise_model(self, height=500, width=500):
        timer = Timer()
        black_image = np.zeros((height, width, 3), dtype = "uint8")
        detections, predictions_dict, shapes = self.detect_image(black_image)
        logging.info("TF model initialised with black image in {}".format(timer.str_timedelta()))
    ##### End #####

    ##### Helpers to draw #####
    @staticmethod
    def get_rgb_in_hue_range(hue_start, hue_end, n_items, lum=1):
        assert n_items > 1

        hue_max_deg = 360
        hue_start /= hue_max_deg
        hue_end /= hue_max_deg

        hue_step = (hue_end - hue_start) / (n_items-1)
        hue_list = []
        for idx in range(n_items):
            out_rgb = hsv_to_rgb(hue_start + idx * hue_step, 1, lum)
            out_bgr = [out_rgb[2], out_rgb[1], out_rgb[0]]
            hue_list.append(out_bgr)
        return np.array(hue_list) * 255
    def assign_color_to_classes(self):
        # color_dict = {'N/A': np.random.uniform(0, 255, size=(3,))}
        # for kkk, vvv in self.category_index.items():
        #     color_dict[vvv['name']] = np.random.uniform(0, 255, size=(3,))
        color_dict = {'N/A': np.array([0,0,0])}

        seeds = ["denari", "spade", "coppe", "bastoni"]

        basic_hue = []
        basic_hue.append(self.get_rgb_in_hue_range(55, 65, 10))
        basic_hue.append(self.get_rgb_in_hue_range(205, 215, 10))
        basic_hue.append(self.get_rgb_in_hue_range(5, 15, 10))
        basic_hue.append(self.get_rgb_in_hue_range(125, 135, 10, 0.4))

        for kkk, vvv in self.category_index.items():
            try:
                ind_seed, ind_num = vvv['name'].split("_")

                idx_seed = seeds.index(ind_seed)
                idx_num = int(ind_num) - 1

                color_dict[vvv['name']] = basic_hue[idx_seed][idx_num]
            except:
                logging.info("Impossible to assign a color to category \"{0}\". Black assigned by default.".format(vvv['name']))
                color_dict[vvv['name']] = np.array([0,0,0])
        self.color_dict = color_dict
    def draw_single_box_on_img(self,
                                img,
                                ymin,
                                xmin,
                                ymax,
                                xmax,
                                color=(255,0,0),
                                thickness=4,
                                display_str_list=(),
                                use_normalized_coordinates=True):

        im_height, im_width, im_channels = img.shape
        if use_normalized_coordinates:
            box = (xmin * im_width, xmax * im_width,
                    ymin * im_height, ymax * im_height)
        else:
            box = (xmin, xmax, ymin, ymax)

        box = tuple(map(int, box))
        (left, right, top, bottom) = box

        cv2.rectangle(img, (left, top), (right, bottom), color, thickness=thickness)

        cv2.putText(img, " ".join(display_str_list), (left, top - 5), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color, 1)
    def draw_boxes_on_img(self,
                        boxes,
                        input_classes,
                        scores,
                        img,
                        score_threshold = None,
                        line_thickness = 4,
                        use_normalized_coordinates = True):

        if not score_threshold:
            score_threshold = self.score_threshold

        box_to_display_str_map = collections.defaultdict(list)
        box_to_color_map = collections.defaultdict(str)

        classes = (input_classes + self.label_id_offset).astype(int)

        for idx in range(boxes.shape[0]):
            if scores is None or scores[idx] > score_threshold:
                box = tuple(boxes[idx].tolist())
                if scores is None:
                    box_to_color_map[box] = 'black'
                else:
                    display_str = ''
                    if classes[idx] in six.viewkeys(self.category_index):
                        class_name = self.category_index[classes[idx]]['name']
                    else:
                        class_name = 'N/A'
                    display_str = str(class_name)
                    if not display_str:
                        display_str = '{}%'.format(round(100*scores[idx]))
                    else:
                        display_str = '{}: {}%'.format(display_str, round(100*scores[idx]))

                    box_to_display_str_map[box].append(display_str)
                    box_to_color_map[box] = self.color_dict[class_name]
                    # box_to_color_map[box] = np.random.uniform(0, 255, size=(3,))

        for box, color in box_to_color_map.items():
            ymin, xmin, ymax, xmax = box
            self.draw_single_box_on_img(
                img,
                ymin,
                xmin,
                ymax,
                xmax,
                color=color,
                thickness=line_thickness,
                display_str_list=box_to_display_str_map[box],
                use_normalized_coordinates=use_normalized_coordinates)
    ##### End #####

    ##### Helpers #####
    def stringify_detections(self, input_detections, score_threshold = None):

        if not score_threshold:
            score_threshold = self.score_threshold

        classes = input_detections['detection_classes'][0].numpy()
        classes = (classes + self.label_id_offset).astype(int)

        scores = input_detections['detection_scores'][0].numpy()

        rel_detections = []
        for idx in range(classes.shape[0]):
            if scores[idx] > score_threshold:
                rel_detections.append(self.category_index[classes[idx]]['name'])
        
        return rel_detections
    def stringify_detections_with_boxes(self, input_detections, score_threshold = None):

        if not score_threshold:
            score_threshold = self.score_threshold

        boxes = input_detections['detection_boxes'][0].numpy()

        classes = input_detections['detection_classes'][0].numpy()
        classes = (classes + self.label_id_offset).astype(int)

        scores = input_detections['detection_scores'][0].numpy()

        rel_detections = []
        for idx in range(classes.shape[0]):
            if scores[idx] > score_threshold:
                box = tuple(boxes[idx].tolist())
                box_class = self.category_index[classes[idx]]['name']
                box_score = scores[idx]

                tmp_detection = {}
                tmp_detection["box"] = box
                tmp_detection["class"] = box_class
                tmp_detection["score"] = float(box_score)

                rel_detections.append(tmp_detection)
        
        return rel_detections
    def get_model_detection_function(self, model):
        @tf.function
        def detect_fn(image):
            """Detect objects in image."""

            image, shapes = model.preprocess(image)
            prediction_dict = model.predict(image, shapes)
            detections = model.postprocess(prediction_dict, shapes)

            return detections, prediction_dict, tf.reshape(shapes, [-1])

        return detect_fn
    def load_image_into_numpy_array(self, path):
        img_data = tf.io.gfile.GFile(path, 'rb').read()
        image = Image.open(BytesIO(img_data))
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)
    ##### End #####

if __name__ == "__main__":
    src_model_path = "/app/tf_models/card_seed_model"
    test_img_path = "/mnt/test_img/"

    card_detector = CardDetector(src_model_path)
    card_detector.load_model()
    card_detector.detect_test_images(test_img_path)

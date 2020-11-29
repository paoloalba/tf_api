import os
import cv2
import logging

import numpy as np

from datetime import datetime

class PersistentImage:

    def __init__(self, persistent_storage):
        self.file_path = None
        self.old_file_path = None
        self.persistent_storage = persistent_storage

        self.time_format = "%Y%m%d_%H%M%S%f"
        self.img_ext = ".jpg"
        self.file_path_template = "displayed_file_{0}.jpg"

    def get_new_file_path(self):
        self.old_file_path = self.file_path
        tmp_file_path = self.file_path_template.format(datetime.now().strftime(self.time_format))
        self.file_path = os.path.join(self.persistent_storage, tmp_file_path)

    def write_img(self, input_img):
        """
        input_img should be generated from something like:
        cv2.imdecode(np.array(), cv2.IMREAD_UNCHANGED)
        """
        self.get_new_file_path()
        cv2.imwrite(self.file_path, input_img)

    def remove_old_img(self):
        if self.old_file_path:
            if os.path.isfile(self.old_file_path):
                os.remove(self.old_file_path)

    def create_black_img(self):
        black_image = np.zeros((500, 500, 3), dtype = "uint8")
        self.black_image_path = os.path.join(self.persistent_storage, "black_image.jpg")
        cv2.imwrite(self.black_image_path, black_image)

    @staticmethod
    def read_img(input_path):
        img_content = None
        if input_path:
            if os.path.isfile(input_path):
                with open(input_path, 'rb') as f:
                    img_content = f.read()
                logging.info("Loaded image from: {0}".format(input_path))
        return img_content

    def read_latest_img(self):
        img_content = self.read_img(self.file_path)
        if img_content is None:
            img_content = self.read_img(self.black_image_path)
        if img_content is None:
            raise Exception("No latest image or backup is available.")

        return img_content
class PersistentBuffer:

    def __init__(self):
        self.buffer = None
        self.img_ext = ".jpg"
    def load_img_to_buffer(self, input_img):
        self.buffer = self.load_img(input_img)
    def load_img(self, input_img):
        """
        input_img should be generated from something like:
        cv2.imdecode(np.array(), cv2.IMREAD_UNCHANGED)
        or like a numpy array directly
        """
        is_success, im_buf_arr = cv2.imencode(self.img_ext, input_img)
        if is_success:
            return im_buf_arr.tobytes()
        else:
            raise Exception("Error in converting image to buffer.")
    def create_black_buffer(self, height=500, width=500):
        black_image = np.zeros((height, width, 3), dtype = "uint8")
        self.black_buffer = self.load_img(black_image)

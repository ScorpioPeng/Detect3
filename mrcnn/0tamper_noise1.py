"""
Mask R-CNN
Train on the nuclei segmentation dataset from the
Kaggle 2018 Data Science Bowl
https://www.kaggle.com/c/data-science-bowl-2018/

Licensed under the MIT License (see LICENSE for details)
Written by Waleed Abdulla

------------------------------------------------------------

Usage: import the module (see Jupyter notebooks for examples), or run from
       the command line as such:

    # Train a new model starting from ImageNet weights
    python3 nucleus.py train --dataset=/path/to/dataset --subset=train --weights=imagenet

    # Train a new model starting from specific weights file
    python3 nucleus.py train --dataset=/path/to/dataset --subset=train --weights=/path/to/weights.h5

    # Resume training a model that you had trained earlier
    python3 nucleus.py train --dataset=/path/to/dataset --subset=train --weights=last

    # Generate submission file
    python3 nucleus.py detect --dataset=/path/to/dataset --subset=train --weights=<last or /path/to/weights.h5>
"""

# Set matplotlib backend
# This has to be done before other importa that might
# set it, but only if we're running in script mode
# rather than being imported.
if __name__ == '__main__':
    import matplotlib
    # Agg backend runs without a display
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

import os
import sys
import json
import datetime
import numpy as np
import skimage.io
import scipy.misc as misc
import sklearn.metrics as me
import sklearn.exceptions
import warnings
import pydensecrf.densecrf as dcrf


warnings.filterwarnings("ignore", category=sklearn.exceptions.UndefinedMetricWarning)

# from imgaug import augmenters as iaa
os.environ['CUDA_VISIBLE_DEVICES'] = '2'

# import tensorflow as tf
# from keras.backend.tensorflow_backend import set_session
# con=tf.ConfigProto()
# con.gpu_options.per_process_gpu_memory_fraction = 0.5
# set_session(tf.Session(config=con))
# Root directory of the project
ROOT_DIR = os.path.abspath("../../")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from mrcnn.config import Config
from mrcnn import utils
from mrcnn import model_noise_single as modellib
from mrcnn import visualize
# from mrcnn import parallel_model

# Path to trained weights file
COCO_WEIGHTS_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.h5")

# Directory to save logs and model checkpoints, if not provided
# through the command line argument --logs
DEFAULT_LOGS_DIR = os.path.join(ROOT_DIR, "logs")

# Results directory
# Save submission files here
RESULTS_DIR = os.path.join(ROOT_DIR, "results/tampers/")




############################################################
#  Configurations
############################################################

class TamperConfig(Config):
    """Configuration for training on the nucleus segmentation dataset."""
    # Give the configuration a recognizable name
    NAME = "tamper"

    GPU_COUNT = 1
    # Adjust depending on your GPU memory
    IMAGES_PER_GPU =1

    # Number of classes (including background)
    NUM_CLASSES = 1 + 1  # Background + nucleus

    # Number of training and validation steps per epoch
    # STEPS_PER_EPOCH = 78641 // IMAGES_PER_GPU
    STEPS_PER_EPOCH = 1000
    VALIDATION_STEPS = 32 // IMAGES_PER_GPU

    # Don't exclude based on confidence. Since we have two classes
    # then 0.5 is the minimum anyway as it picks between nucleus and BG
    # DETECTION_MIN_CONFIDENCE = 0

    # Backbone network architecture
    # Supported values are: resnet50, resnet101
    BACKBONE = "resnet50"

    # Input image resizing
    # Random crops of size 512x512
    # IMAGE_RESIZE_MODE = "crop"
    # IMAGE_MIN_DIM = 512
    # IMAGE_MAX_DIM = 512
    # IMAGE_MIN_SCALE = 2.0

    # # Length of square anchor side in pixels
    # RPN_ANCHOR_SCALES = (8, 16, 32, 64, 128)

    # # ROIs kept after non-maximum supression (training and inference)
    # POST_NMS_ROIS_TRAINING = 1000
    # POST_NMS_ROIS_INFERENCE = 2000

    # # Non-max suppression threshold to filter RPN proposals.
    # # You can increase this during training to generate more propsals.
    # RPN_NMS_THRESHOLD = 0.9

    # # How many anchors per image to use for RPN training
    # RPN_TRAIN_ANCHORS_PER_IMAGE = 64

    # # Image mean (RGB)
    # MEAN_PIXEL = np.array([43.53, 39.56, 48.22])

    # # If enabled, resizes instance masks to a smaller size to reduce
    # # memory load. Recommended when using high-resolution images.
    # USE_MINI_MASK = True
    # MINI_MASK_SHAPE = (56, 56)  # (height, width) of the mini-mask

    # # Number of ROIs per image to feed to classifier/mask heads
    # # The Mask RCNN paper uses 512 but often the RPN doesn't generate
    # # enough positive proposals to fill this and keep a positive:negative
    # # ratio of 1:3. You can increase the number of proposals by adjusting
    # # the RPN NMS threshold.
    # TRAIN_ROIS_PER_IMAGE = 128

    # # Maximum number of ground truth instances to use in one image
    # MAX_GT_INSTANCES = 200

    # # Max number of final detections per image
    # DETECTION_MAX_INSTANCES = 400


class TamperInferenceConfig(TamperConfig):
    # Set batch size to 1 to run one image at a time
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    # Don't resize imager for inferencing
    # IMAGE_RESIZE_MODE = "pad64"
    # Non-max suppression threshold to filter RPN proposals.
    # You can increase this during training to generate more propsals.
    # RPN_TRAIN_ANCHORS_PER_IMAGE = 500
    RPN_NMS_THRESHOLD = 0.9
    # DETECTION_MAX_INSTANCES = 300
    # DETECTION_NMS_THRESHOLD = 0.7

############################################################
#  Dataset
############################################################

class TamperDataset(utils.Dataset):

    def load_tamper(self, dataset_dir, subset):
        """Load a subset of the nuclei dataset.

        dataset_dir: Root directory of the dataset
        subset: Subset to load. Either the name of the sub-directory,
                such as stage1_train, stage1_test, ...etc. or, one of:
                * train: stage1_train excluding validation images
                * val: validation images from VAL_IMAGE_IDS
        """
        # Add classes. We have one class.
        # Naming the dataset nucleus, and the class nucleus
        self.add_class("tampers", 1, "tampers")

        # Which subset?
        # "val": use hard-coded list above
        # "train": use data from stage1_train minus the hard-coded list above
        # else: use the data from the specified sub-directory
        # assert subset in ["train", "val", "stage1_train", "stage1_test", "stage2_test"]
        # subset_dir = "stage1_train" if subset in ["train", "val"] else subset
        dataset_dir = os.path.join(dataset_dir, subset, 'images')
        if subset == "val" or subset == "test":
            image_ids = next(os.walk(dataset_dir))[2]
        else:
            # Get image ids from directory names
            image_ids = next(os.walk(dataset_dir))[2]
        

        # dircopy_move = '/data/twj/copy-move/data_zoo/dataset/images/train'
        # image_ids_copy_move = next(os.walk(os.path.join(dircopy_move, 'images')))[2]

        # dirnew_splicing = '/data/tamper'
        # image_ids_new_splicing = next(os.walk(os.path.join(dirnew_splicing, 'images')))[2]

        # dircopy_move = '/home/as/deeplab/wpmrcnn/ca2new/test'
        # image_ids_copy_move = next(os.walk(os.path.join(dircopy_move, 'images')))[2]

           
        # dircopy_move = '/data/gy/ca2att/train3'
        # image_ids_copy_move = next(os.walk(os.path.join(dircopy_move, 'images')))[2]

        # # # dirtxt_sp = '/data/gy/tamperpre/train'
        # # # image_ids_txt_sp = next(os.walk(os.path.join(dirtxt_sp, 'images')))[2]

        # dirnew_sp = '/data/gy/c2newsp/train'
        # image_ids_new_sp = next(os.walk(os.path.join(dirnew_sp, 'images')))[2]

        # Add images
        for image_id in image_ids:
            self.add_image(
                "tampers",
                image_id=image_id[:-4],
                path=os.path.join(dataset_dir, image_id))

        # for image_id in image_ids_copy_move:
        #     self.add_image(
        #         "tampers",
        #         image_id=image_id[:-4],
        #         path=os.path.join(dircopy_move, 'images', image_id))

        # for image_id in image_ids_new_splicing:
        #     self.add_image(
        #         "tampers",
        #         image_id=image_id[:-4],
        #         path=os.path.join(dirnew_splicing, 'images', image_id))

        # # for image_id in image_ids_txt_sp:
        # #     self.add_image(
        # #         "tampers",
        # #         image_id=image_id[:-4],
        # #         path=os.path.join(dirtxt_sp, 'images', image_id))

        # for image_id in image_ids_new_sp:
        #     self.add_image(
        #         "tampers",
        #         image_id=image_id[:-4],
        #         path=os.path.join(dirnew_sp, 'images', image_id))

    def load_mask(self, image_id):
        """Generate instance masks for an image.
       Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        info = self.image_info[image_id]
        # Get mask directory from image path
        mask_dir = os.path.join(os.path.dirname(os.path.dirname(info['path'])), "masks")

        # Read mask files from .png image
        mask = []
        # for f in next(os.walk(mask_dir))[2]:
        m = skimage.io.imread(os.path.join(mask_dir, info['id']+'.png')).astype(np.bool)
        mask.append(m)
            # print(mask)
        mask = np.stack(mask, axis=-1)
        # Return mask, and array of class IDs of each instance. Since we have
        # one class ID, we return an array of ones
        return mask, np.ones([mask.shape[-1]], dtype=np.int32)

    def load_ela(self, image_id):
        """Generate instance masks for an image.
       Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        # info = self.image_info[image_id]
        # # Get mask directory from image path
        # ela_dir = os.path.join(os.path.dirname(os.path.dirname(info['path'])), "elas")

        # # Read mask files from .png image
        # ela = []
        # # for f in next(os.walk(mask_dir))[2]:
        # e = skimage.io.imread(os.path.join(ela_dir, info['id']+'.jpg')).astype(np.float32)
        # ela.append(e)
        #     # print(mask)
        # ela = np.stack(ela, axis=-1)
        # # Return mask, and array of class IDs of each instance. Since we have
        # # one class ID, we return an array of ones
        # return ela
        info = self.image_info[image_id]
        ela_dir=os.path.join(os.path.dirname(os.path.dirname(info['path'])), "elas")
        image = skimage.io.imread(os.path.join(ela_dir, info['id']+".jpg"))
        # If grayscale. Convert to RGB for consistency.
        if image.ndim != 3:
            image = skimage.color.gray2rgb(image)
        # If has an alpha channel, remove it for consistency
        if image.shape[-1] == 4:
            image = image[..., :3]
        return image



    def load_annaation(self, image_id):
        """Generate instance masks for an image.
       Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        info = self.image_info[image_id]
        # Get mask directory from image path
        mask_dir = os.path.join(os.path.dirname(os.path.dirname(info['path'])), "masks")


        m = skimage.io.imread(os.path.join(mask_dir, info['id']+'.png')) / 255

        return m

    def image_reference(self, image_id):
        """Return the path of the image."""
        info = self.image_info[image_id]
        if info["source"] == "tampers":
            return info["id"]
        else:
            super(self.__class__, self).image_reference(image_id)


############################################################
#  Training
############################################################

def save_image(image, save_dir, name, mean=None):
    """
    Save image by unprocessing if mean given else just save
    :param mean:
    :param image:
    :param save_dir:
    :param name:
    :return:
    """
    if mean:
        image = unprocess_image(image, mean)
    misc.imsave(os.path.join(save_dir, name + ".png"), image)

def train(model, dataset_dir, subset):
    """Train the model."""
    # Training dataset.
    dataset_train = TamperDataset()
    dataset_train.load_tamper(dataset_dir, subset)
    dataset_train.prepare()

    print(len(dataset_train.image_ids))
    # print(dataset_train.image_info)

    # Validation dataset
    dataset_val = TamperDataset()
    dataset_val.load_tamper(dataset_dir, "val")
    dataset_val.prepare()
    # print(dataset_val.image_info)

    # Image augmentation
    # http://imgaug.readthedocs.io/en/latest/source/augmenters.html
    # augmentation = iaa.SomeOf((0, 2), [
    #     iaa.Fliplr(0.5),
    #     iaa.Flipud(0.5),
    #     iaa.OneOf([iaa.Affine(rotate=90),
    #                iaa.Affine(rotate=180),
    #                iaa.Affine(rotate=270)]),
    #     iaa.Multiply((0.8, 1.5)),
    #     iaa.GaussianBlur(sigma=(0.0, 5.0))
    # ])

    # *** This training schedule is an example. Update to your needs ***

    # If starting from imagenet, train heads only for a bit
    # since they have random weights
    print("Train network all")
    # model.train(dataset_train, dataset_val,
    #             learning_rate=config.LEARNING_RATE,
    #             epochs=20,
    #             augmentation=augmentation,
    #             layers='heads')
    model.train(dataset_train, dataset_val,
                learning_rate=config.LEARNING_RATE,
                epochs=1200,
                layers='all')


    # print("Train all layers")
    # # model.train(dataset_train, dataset_val,
    # #             learning_rate=config.LEARNING_RATE,
    # #             epochs=40,
    # #             augmentation=augmentation,
    # #             layers='all')
    # model.train(dataset_train, dataset_val,
    #             learning_rate=config.LEARNING_RATE,
    #             epochs=160,
    #             layers='all')

############################################################
#  RLE Encoding
############################################################

def rle_encode(mask):
    """Encodes a mask in Run Length Encoding (RLE).
    Returns a string of space-separated values.
    """
    assert mask.ndim == 2, "Mask must be of shape [Height, Width]"
    # Flatten it column wise
    m = mask.T.flatten()
    # Compute gradient. Equals 1 or -1 at transition points
    g = np.diff(np.concatenate([[0], m, [0]]), n=1)
    # 1-based indicies of transition points (where gradient != 0)
    rle = np.where(g != 0)[0].reshape([-1, 2]) + 1
    # Convert second index in each pair to lenth
    rle[:, 1] = rle[:, 1] - rle[:, 0]
    return " ".join(map(str, rle.flatten()))


def rle_decode(rle, shape):
    """Decodes an RLE encoded list of space separated
    numbers and returns a binary mask."""
    rle = list(map(int, rle.split()))
    rle = np.array(rle, dtype=np.int32).reshape([-1, 2])
    rle[:, 1] += rle[:, 0]
    rle -= 1
    mask = np.zeros([shape[0] * shape[1]], np.bool)
    for s, e in rle:
        assert 0 <= s < mask.shape[0]
        assert 1 <= e <= mask.shape[0], "shape: {}  s {}  e {}".format(shape, s, e)
        mask[s:e] = 1
    # Reshape and transpose
    mask = mask.reshape([shape[1], shape[0]]).T
    return mask


def mask_to_rle(image_id, mask, scores):
    "Encodes instance masks to submission format."
    assert mask.ndim == 3, "Mask must be [H, W, count]"
    # If mask is empty, return line with image ID only
    if mask.shape[-1] == 0:
        return "{},".format(image_id)
    # Remove mask overlaps
    # Multiply each instance mask by its score order
    # then take the maximum across the last dimension
    order = np.argsort(scores)[::-1] + 1  # 1-based descending
    mask = np.max(mask * np.reshape(order, [1, 1, -1]), -1)
    # Loop over instance masks
    lines = []
    for o in order:
        m = np.where(mask == o, 1, 0)
        # Skip if empty
        if m.sum() == 0.0:
            continue
        rle = rle_encode(m)
        lines.append("{}, {}".format(image_id, rle))
    return "\n".join(lines)


############################################################
#  Detection
############################################################
def dense_crf(img, output_probs):
    h = output_probs.shape[0]
    w = output_probs.shape[1]

    output_probs = np.expand_dims(output_probs, 0)
    output_probs = np.append(1 - output_probs, output_probs, axis=0)
    output_probs = output_probs.astype(np.float32)
    d = dcrf.DenseCRF2D(w, h, 2)
    U = -np.log(output_probs)
    U = U.reshape((2, -1))
    U = np.ascontiguousarray(U)
    img = np.ascontiguousarray(img)

    d.setUnaryEnergy(U)

    # d.addPairwiseGaussian(sxy=3, compat=3)
    # d.addPairwiseBilateral(sxy=20, srgb=3, rgbim=img, compat=10)
    d.addPairwiseGaussian(sxy=3, compat=3)
    d.addPairwiseBilateral(sxy=30, srgb=5, rgbim=img, compat=3)
    Q = d.inference(10)
    Q = np.argmax(np.array(Q), axis=0).reshape((h, w))

    return Q


def get_FM(prediction, label):

    f1 = me.f1_score(label.flatten(), prediction.flatten())
    return f1

def detect(model, dataset_dir, subset):
    """Run detection on images in the given directory."""
    print("Running on {}".format(dataset_dir))

    # Create directory
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    submit_dir = "submit_{:%Y%m%dT%H%M%S}".format(datetime.datetime.now())
    submit_dir = os.path.join(RESULTS_DIR, submit_dir)
    os.makedirs(submit_dir)

    # Read dataset
    dataset = TamperDataset()
    dataset.load_tamper(dataset_dir, subset)
    dataset.prepare()
    # Load over images
    submission = []
    f1 = 0
    print(len(dataset.image_ids))
    # for image_id in dataset.image_ids:
    #     # Load image and run detection
    #     image = dataset.load_image(image_id)
    #     # Detect objects
    #     r = model.detect([image], verbose=0)[0]

    #     # Encode image to RLE. Returns a string of multiple lines
    #     source_id = dataset.image_info[image_id]["id"]
    #     rle = mask_to_rle(source_id, r["masks"], r["scores"])
    #     submission.append(rle)
    #     # Save image with masks

    #     N = r["scores"].shape[0]
    #     if not N:
    #     	H, W, C = image.shape
    #     	mask = np.zeros((H,W))

        	
    #     else:

    #         H, W, C = image.shape

    #         idx = np.argsort(-r["scores"])
    #         mask = r["masks"][:,:,idx[0]].astype(np.float32)

    #         bbox = r["rois"][idx[0], :4]

    #         y1, x1, y2, x2 = bbox



    #         mask = dense_crf(image, mask)

    #         mask = np.where(mask >= 0.5, 255, 0)

            # H, W, C = image.shape

            # full_mask = np.zeros((H, W))
            # full_mask[y1:y2, x1:x2] = mask

    for image_id in dataset.image_ids:
        # Load image and run detection
        image = dataset.load_image(image_id)
        # ela=dataset.load_ela(image_id)
        # Detect objects
        # r = model.detect([image],[ela], verbose=0)[0]
        r = model.detect([image],verbose=0)[0]

        # Encode image to RLE. Returns a string of multiple lines
        source_id = dataset.image_info[image_id]["id"]
        rle = mask_to_rle(source_id, r["masks"], r["scores"])
        submission.append(rle)
        # Save image with masks

        N = r["scores"].shape[0]
        if not N:
            H, W, C = image.shape
            mask = np.zeros((H,W))

            
        else:
            idx = np.argsort(-r["scores"])
            mask = r["masks"][:,:,idx[0]].astype(np.uint8)

        # save_image(mask, submit_dir, name=dataset.image_info[image_id]["id"])  


        annotation = dataset.load_annaation(image_id)
        annotation = np.where(annotation >= 0.5, 1, 0)       
        f = get_FM(mask, annotation)
        f1 += f

    print(f1/len(dataset.image_ids))




        # save_image(mask, submit_dir, name=dataset.image_info[image_id]["id"])        

        # visualize.display_instances(
        #     image, r['rois'], r['masks'], r['class_ids'],
        #     dataset.class_names, r['scores'],
        #     show_bbox=False, show_mask=False,
        #     title="Predictions")
        # plt.savefig("{}/{}.png".format(submit_dir, dataset.image_info[image_id]["id"]))

    # Save to csv file
    # submission = "ImageId,EncodedPixels\n" + "\n".join(submission)
    # file_path = os.path.join(submit_dir, "submit.csv")
    # with open(file_path, "w") as f:
    #     f.write(submission)
    print("Saved to ", submit_dir)


############################################################
#  Command Line
############################################################

if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Mask R-CNN for nuclei counting and segmentation')
    parser.add_argument("command",
                        metavar="<command>",
                        help="'train' or 'detect'",default="train")
    parser.add_argument('--dataset', required=False,
                        metavar="/path/to/dataset/",
                        help='Root directory of the dataset',default="/data/")
    parser.add_argument('--weights', required=True,
                        metavar="/path/to/weights.h5",
                        help="Path to weights .h5 file or 'coco'")
    parser.add_argument('--logs', required=False,
                        default=DEFAULT_LOGS_DIR,
                        metavar="/path/to/logs/",
                        help='Logs and checkpoints directory (default=logs/)')
    parser.add_argument('--subset', required=False,
                        metavar="Dataset sub-directory",
                        help="Subset of dataset to run prediction on",default="train")
    args = parser.parse_args()

    # Validate arguments
    if args.command == "train":
        assert args.dataset, "Argument --dataset is required for training"
    elif args.command == "detect":
        assert args.subset, "Provide --subset to run prediction on"

    print("Weights: ", args.weights)
    print("Dataset: ", args.dataset)
    if args.subset:
        print("Subset: ", args.subset)
    print("Logs: ", args.logs)

    # Configurations
    if args.command == "train":
        config = TamperConfig()
    else:
        config = TamperInferenceConfig()
    config.display()

    # Create model
    if args.command == "train":
        model = modellib.MaskRCNN(mode="training", config=config,
                                  model_dir=args.logs)




    else:
        model = modellib.MaskRCNN(mode="inference", config=config,
                                  model_dir=args.logs)

    # Select weights file to load
    if args.weights.lower() == "coco":
        weights_path = COCO_WEIGHTS_PATH
        # Download weights file
        if not os.path.exists(weights_path):
            utils.download_trained_weights(weights_path)
    elif args.weights.lower() == "last":
        # Find last trained weights
        weights_path = model.find_last()
    elif args.weights.lower() == "imagenet":
        # Start from ImageNet trained weights
        weights_path = model.get_imagenet_weights()
    else:
        weights_path = args.weights

    # Load weights
    print("Loading weights ", weights_path)
    if args.weights.lower() == "coco":
        # Exclude the last layers because they require a matching
        # number of classes
        model.load_weights(weights_path, by_name=True, exclude=[
            "mrcnn_class_logits", "mrcnn_bbox_fc",
            "mrcnn_bbox", "mrcnn_mask"])
    else:
        model.load_weights(weights_path, by_name=True)

    # Train or evaluate
    if args.command == "train":
        train(model, args.dataset, args.subset)
    elif args.command == "detect":
        detect(model, args.dataset, args.subset)
    else:
        print("'{}' is not recognized. "
              "Use 'train' or 'detect'".format(args.command))

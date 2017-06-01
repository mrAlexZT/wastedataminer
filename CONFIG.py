# BACKEND - APP.PY
_VERSION_ = "v0.2.4"
_FOLDER_4_LEARN_ = "files4learning"
_FOLDER_4_RCGN_ = "files4recognition"
_IMAGE_FULL_PATH_ = 'CNN/image.jpg'		# Where to save the trained graph.
_MODEL_FULL_PATH_ = '20170530/output_graph.pb'	# Where to save the trained graph\'s labels.
_LABELS_FULL_PATH_ = '20170530/output_labels.txt'
_LOG_FULL_PATH_ ="RUN_LOGS"
_PLACE_WASTE_DB_ = "place-waste.csv"
_WASTE_DB_ = "waste_db.csv"
_THREADED_RUN_ = True

# RETRAIN
_LOG_DIR_ = "LOGS" # Where to save summary logs for TensorBoard
_BOTTLENECK_DIR_ = "CNN/bottleneck" # Path to cache bottleneck layer values as files.
_MODEL_DIR_ = "CNN/imagenet" # Path to classify_image_graph_def.pb, 
						# magenet_synset_to_human_label_map.txt, 
						# and imagenet_2012_challenge_label_map_proto.pbtxt.
_DATASET_ = "/home/starforge/DS/DATASETS/dataset_170530" # Path to folders of labeled images.
# _IMAGE_FULL_PATH_ = 'image.jpg'		# Where to save the trained graph.
# _MODEL_FULL_PATH_ = 'output_graph.pb'		# Where to save the trained graph\'s labels.
_FLIP_LEFT_RIGHT_ = False 	# Whether to randomly flip half of the training images horizontally.
_RANDOM_CROP_ = 0 		# A percentage determining how much of a margin to randomly crop off the training images.
_RANDOM_BRIGHNESS_ = 0		# A percentage determining how much to randomly multiply the training image input pixels up or down by.
_RANDOM_SCALE_ = 0		# A percentage determining how much to randomly scale up the size of the training images by

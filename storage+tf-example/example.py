import tensorflow as tf
import argparse
import re
from google.cloud import storage

SOURCE_BUCKET_NAME = 
SOURCE_PATH = 
parce = argparse.ArgumentParser()
parce.add_argument('--job-dir', required=True)

def get_storage_place(args: argparse.Namespace)-> tuple:
    '''
    get bucket name and path of the directory for storage requested by
    the submit_training_job command 
    '''
    pattern = 'gs:\/\/([a-z0-9-]+)\/(.+)$' # for regex matching
    full_path = args.job_dir     # argparse converts to underscores
    bucket_name = re.search(pattern, full_path).group(1)
    remote_directory = re.search(pattern, full_path).group(2)
    if remote_directory[-1] != '/': # add trailing slash if not present
        remote_directory += '/'
    return bucket_name , remote_directory  

storage_client = storage.Client() 

# get list of images to download and process
jpegs = list(storage_client.list_blobs(SOURCE_BUCKET_NAME, prefix=SOURCE_PATH))
# download images to remote worker first 
for file in jpegs[:10]:
    file.download_to_filename(file.name.rsplit('/',1)[-1])
    
    
# process images in remote worker with tensorflow
# resize and make b&w
for file in jpegs[:10]:
    raw = tf.io.read_file(file.name.rsplit('/',1)[-1])
    img = tf.io.decode_image(raw)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, [200,200])
    img = tf.image.rgb_to_grayscale(img)
    tf.io.write_file(file.name.rsplit('/',1)[-1], 
                     tf.io.encode_jpeg(tf.image.convert_image_dtype(img, tf.uint8)))
    
# get name of current project's shared bucket
args = parce.parse_args()
BUCKET_NAME, remote_dir = get_storage_place(args)
bucket = storage.Client().bucket(BUCKET_NAME)

# upload files from remote worker to storage bucket
for i in range(10):
    blob = bucket.blob(f"tf_io/{jpegs[i].name.rsplit('/',1)[-1]}")
    blob.upload_from_filename(jpegs[i].name.rsplit('/',1)[-1])
    
print('Success')
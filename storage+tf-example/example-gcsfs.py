import os
import tensorflow as tf
import argparse
import re
import gcsfs
import requests

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

def get_project_id()-> str:
    url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    response = requests.get(
        url,
        headers={"Metadata-Flavor":"Google"})
    return response.text

storage_client = gcsfs.GCSFileSystem(project=get_project_id())

# get list of images to download 
SOURCE_PATH = 
jpegs = storage_client.ls(SOURCE_PATH)

# download images to remote worker first 
for file in jpegs[:10]:
    storage_client.download(file, file.rsplit('/', 1)[-1])
    
# process images in remote worker with tensorflow
# resize and make b&w
for file in jpegs[:10]:
    raw = tf.io.read_file(file.rsplit('/',1)[-1])
    img = tf.io.decode_image(raw)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, [200,200])
    img = tf.image.rgb_to_grayscale(img)
    tf.io.write_file(file.rsplit('/',1)[-1], 
                     tf.io.encode_jpeg(tf.image.convert_image_dtype(img, tf.uint8)))
    
# get name of current project's shared bucket
args = parce.parse_args()
BUCKET_NAME, remote_dir = get_storage_place(args)

# upload files from remote worker to storage bucket
for file in jpegs[:10]:
    storage_client.put(file.rsplit('/',1)[-1], os.path.join(BUCKET_NAME, f"gcsfs_io/{file.rsplit('/',1)[-1]}"))
    
print('Success')
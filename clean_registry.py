'''
Removes all images in the registry minus those explicitly asked to be kept. The script will run two passes,
in the first one only images with the default tag will be deleted and a list of dangling images will be created
(you can ignore the error messages). In the second pass all remaining images will be erased.
TODO: replace gcloud command calls with docker registry API calls:
https://cloud.google.com/container-registry/docs/reference/docker-api
'''
import subprocess
import requests
import re
import argparse

project = requests.get(
            'http://metadata.google.internal/computeMetadata/v1/project/project-id',
            headers={"Metadata-Flavor": "Google"}).text

def parcero():
    line0 = 'Removes all images in the registry minus those explicitly asked to be kept. The script will run two passes,\n'
    line1 = 'in the first one only images with the default tag will be deleted and a list of dangling images will be created\n'
    line2 = '(you can ignore the error messages). In the second pass all remaining images will be erased.'
    huyparce = argparse.ArgumentParser(description=line0 + line1 + line2, formatter_class=argparse.RawTextHelpFormatter)
    huyparce.add_argument('--names-list', nargs='+', type=str,
                          help='Names of images to be kept in the registry', metavar='image_name')
    huyparce.add_argument('--hostname', type=str,
                          help='Container registry host name', default='us.gcr.io', metavar='gcr.io')
    return huyparce.parse_args()

def filter_image(image: str, names: list)-> bool:
    return ('gcr.' in image) and not any(x in image for x in names)

def get_images(project: str, names: None, host: str = 'us.gcr.io')-> list:
    output = subprocess.run(f'gcloud container images list --repository={host}/{project}',
                            shell=True, capture_output=True).stdout.decode('utf-8').split('\n')
    if names is not None:
        return [x for x in output if filter_image(x, names)]
    else:
        return [x for x in output if 'gcr.' in x]

def try_remove(images: list)-> list:
    individual = []
    for image in images:
        out = subprocess.run(f'gcloud container images delete {image} --force-delete-tags  --quiet',
                             shell=True)
        if out.returncode > 0:
            tmp = subprocess.run(f'gcloud container images list-tags {image}',
                                 shell=True, capture_output=True).stdout.decode('utf-8').split('\n')
            digests = [x.split()[0] for x in tmp if re.match('[a-z0-9]+', x[0:12])]
            if len(digests) > 0:
                individual.extend([image + '@sha256:' + d for d in digests])
    return individual
    

if __name__ == '__main__':
    arguments = parcero()
    images = get_images(project, arguments.names_list, arguments.hostname)
    remaining_img = try_remove(images)
    if len(remaining_img) > 0:
        remaining_img = try_remove(remaining_img)

    if len(remaining_img) > 0:
        print('Inspect these remaining images individually:')
        for x in remaining_img:
            print(x)
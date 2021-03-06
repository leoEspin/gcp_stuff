'''
Removes all images in the registry minus those explicitly asked to be kept. 
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
    line0 = 'Removes all images in the registry minus those explicitly asked to be kept.'
    huyparce = argparse.ArgumentParser(description=line0, formatter_class=argparse.RawTextHelpFormatter)
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
    remaining = []
    for image in images:
        tmp = subprocess.run(f'gcloud container images list-tags {image}',
                             shell=True, capture_output=True).stdout.decode('utf-8').split('\n')
        digests = [x.split()[0] for x in tmp if re.match('[a-z0-9]+', x[0:12])]
        if len(digests) > 0:
            individual.extend([image + '@sha256:' + d for d in digests])
        
        while len(individual) > 0:
            single = individual.pop()
            out = subprocess.run(f'gcloud container images delete {single} --force-delete-tags  --quiet',
                                 shell=True)
            if out.returncode > 0:
                remaining.append(single)
            
    return remaining
    

if __name__ == '__main__':
    arguments = parcero()
    images = get_images(project, arguments.names_list, arguments.hostname)
    if arguments.names_list is not None:
        input(f"{len(images)} images will be deleted, and {len(arguments.names_list)} will be kept. Press Enter to continue...")
    else:
        input(f"{len(images)} images will be deleted. Press Enter to continue...")
    remaining_img = try_remove(images)

    if len(remaining_img) > 0:
        print('Inspect these remaining images individually:')
        for x in remaining_img:
            print(x)
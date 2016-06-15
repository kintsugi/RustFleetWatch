import cv2
import argparse

parser = argparse.ArgumentParser(description='Split a video file into frames')

parser.add_argument('-i', dest='input', required=True)
parser.add_argument('-o', dest='output', required=True)

args = parser.parse_args()
vid = cv2.VideoCapture(args.input)

j = 0

while vid.isOpened():
    success,im=vid.read()
    cv2.imwrite('{0}/frame{1}.jpg'.format(args.output, j),im)
    j+=1

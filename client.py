#!/usr/bin/env python
"""OpenCV Client to Display TCP Kinect Data Stream"""
import cv
import zmq
import numpy as np
import kinectfs_pb2
import cmdparse


def array2cv(a):
    dtype2depth = {'uint8': cv.IPL_DEPTH_8U,
                   'int8': cv.IPL_DEPTH_8S,
                   'uint16': cv.IPL_DEPTH_16U,
                   'int16': cv.IPL_DEPTH_16S,
                   'int32': cv.IPL_DEPTH_32S,
                   'float32': cv.IPL_DEPTH_32F,
                   'float64': cv.IPL_DEPTH_64F}
    try:
        nChannels = a.shape[2]
    except IndexError:
        nChannels = 1
    cv_im = cv.CreateImageHeader((a.shape[1], a.shape[0]),
                                 dtype2depth[str(a.dtype)],
                                 nChannels)
    cv.SetData(cv_im, a.tostring(),
               a.dtype.itemsize*nChannels*a.shape[1])
    return cv_im


def recv(socket):
    f = kinectfs_pb2.KinectMessage.FromString(socket.recv()).frame
    if f.type == f.FREENECT_DEPTH_11BIT:
        frame_type = 'depth'
        data = np.fromstring(f.data,
                             dtype=np.uint16).reshape((f.height, f.width))
    elif f.type == f.FREENECT_VIDEO_RGB:
        frame_type = 'video'
        data = np.fromstring(f.data,
                             dtype=np.uint8).reshape((f.height, f.width, 3))
    else:
        raise TypeError('Unsupported Type: %s' % (f.type))
    return frame_type, data, f.timestamp


def main(address, port):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.HWM, 10)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    print('Connecting to [%s:%d]' % (address, port))
    socket.connect("tcp://%s:%d" % (address, port))
    cv.NamedWindow('Depth')
    cv.NamedWindow('Video')
    while True:
        frame_type, data, timestamp = recv(socket)
        if frame_type == 'depth':
            cv.ShowImage('Depth', array2cv(data.astype(np.uint8)))
        else:
            cv.ShowImage('Video', array2cv(data[:, :, ::-1].astype(np.uint8)))
        cv.WaitKey(10)


if __name__ == '__main__':
    main(*cmdparse.address_port(__doc__))

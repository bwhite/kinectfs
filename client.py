import cv
import zmq
import numpy as np


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
    except:
        nChannels = 1
    cv_im = cv.CreateImageHeader((a.shape[1], a.shape[0]),
                                 dtype2depth[str(a.dtype)],
                                 nChannels)
    cv.SetData(cv_im, a.tostring(),
               a.dtype.itemsize*nChannels*a.shape[1])
    return cv_im


def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.HWM, 10)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    socket.connect("tcp://127.0.0.1:5000")
    cv.NamedWindow('Depth')
    cv.NamedWindow('Video')
    while True:
        frame_type, data, timestamp = socket.recv_pyobj()
        if frame_type == 'depth':
            cv.ShowImage('Depth', array2cv(data.astype(np.uint8)))
        else:
            cv.ShowImage('Video', array2cv(data[:, :, ::-1].astype(np.uint8)))
        cv.WaitKey(10)

if __name__ == '__main__':
    main()

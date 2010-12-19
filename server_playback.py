#!/usr/bin/env python
"""Kinect Data Stream Dump Playback Server (supports multiple clients)

This takes in the output from client_record.py and streams it as if
this server had the original kinect plugged in.  Delays are recreated
as faithfully as possible.
"""
import zmq
import numpy as np
import time
import kinectfs_pb2
import cmdparse


def main(address, port, path):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.HWM, 10)
    print('Listening on [%s:%d]' % (address, port))
    socket.bind("tcp://%s:%d" % (address, port))
    prev_wall_time = None
    prev_proc_time = None
    print('Reading from [%s]' % (path))
    with open(path) as fp:
        while True:
            try:
                sz = np.fromstring(fp.read(4), dtype=np.uint32)[0]
            except IndexError:
                break
            m = fp.read(sz)
            f = kinectfs_pb2.KinectMessage.FromString(m).frame
            try:
                delay = max(0., (f.wall_time - prev_wall_time) -
                            (time.time() - prev_proc_time))
            except TypeError:
                delay = 0.
            time.sleep(delay)
            socket.send(m)
            prev_wall_time = f.wall_time
            prev_proc_time = time.time()
        print('End of recording')


if __name__ == '__main__':
    main(*cmdparse.address_port_file(__doc__))

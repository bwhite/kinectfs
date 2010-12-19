#!/usr/bin/env python
"""Client to record a Kinect Data Stream

To stop recording use Ctrl-C, it will cleanly shutdown.
"""
import zmq
import numpy as np
import signal
import cmdparse


keep_running = True


def handler(signum, frame):
    global keep_running
    keep_running = False
    print('Stopping...')


def main(address, port, path):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.HWM, 10)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    print('Connecting to [%s:%d]' % (address, port))
    socket.connect("tcp://%s:%d" % (address, port))
    print('Recording to [%s]' % (path))
    with open(path, 'w') as fp:
        while keep_running:
            m = socket.recv()
            fp.write(np.uint32(len(m)).tostring())
            fp.write(m)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main(*cmdparse.address_port_path(__doc__))

#!/usr/bin/env python
"""Kinect Data Stream Server (supports multiple clients)"""
import freenect
import functools
import zmq
import time
import kinectfs_pb2
import cmdparse

state = None
state_wall_time = None


def send_frame(socket, frame_type, dev, data, timestamp):
    f = kinectfs_pb2.KinectMessage.KinectFrame(data=data.tostring(),
                                               type=frame_type,
                                               timestamp=timestamp,
                                               wall_time=time.time())
    try:
        f.height, f.width, f.channels = data.shape[:3]
    except ValueError:
        (f.height, f.width), f.channels = data.shape[:2], 1
    m = kinectfs_pb2.KinectMessage(frame=f)
    try:
        m.tilt_state.accelerometer_x = state.accelerometer_x
        m.tilt_state.accelerometer_y = state.accelerometer_y
        m.tilt_state.accelerometer_z = state.accelerometer_z
        m.tilt_state.tilt_angle = state.tilt_angle
        m.tilt_state.tilt_status = state.tilt_status
        m.tilt_state.wall_time = state_wall_time
    except AttributeError:
        print('Tilt not updated!')
    socket.send(m.SerializeToString())


def update_tilt(dev, ctx):
    global state, state_wall_time
    freenect.update_tilt_state(dev)
    state = freenect.get_tilt_state(dev)
    state_wall_time = time.time()


def main(address, port):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.HWM, 10)
    print('Listening on [%s:%d]' % (address, port))
    socket.bind("tcp://%s:%d" % (address, port))
    depth_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_DEPTH_11BIT
    video_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_VIDEO_RGB
    depth = functools.partial(send_frame, socket, depth_type)
    video = functools.partial(send_frame, socket, video_type)
    freenect.runloop(depth=depth,
                     video=video,
                     body=update_tilt)


if __name__ == '__main__':
    main(*cmdparse.address_port(__doc__))

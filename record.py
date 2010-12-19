#!/usr/bin/env python
"""Kinect Data Stream Server (supports multiple clients)"""
import freenect
import functools
import signal
import time
import kinectfs_pb2
import cmdparse
import numpy as np

state = None
state_wall_time = None
keep_running = True
fp = None
total_frames_rgb = 0
total_frames_depth = 0


def save_frame(frame_type, dev, data, timestamp):
    global total_frames_rgb, total_frames_depth
    f = kinectfs_pb2.KinectMessage.KinectFrame(data=data.tostring(),
                                               type=frame_type,
                                               timestamp=timestamp,
                                               wall_time=time.time())
    try:
        total_frames_rgb += 1
        f.height, f.width, f.channels = data.shape[:3]
    except ValueError:
        total_frames_depth += 1
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
    s = m.SerializeToString()
    fp.write(np.uint32(len(s)).tostring())
    fp.write(s)


def handler(signum, frame):
    global keep_running
    keep_running = False
    print('Stopping...')


def update_tilt(dev, ctx):
    global state, state_wall_time
    if not keep_running:
        raise freenect.Kill
    freenect.update_tilt_state(dev)
    state = freenect.get_tilt_state(dev)
    state_wall_time = time.time()


def main(path):
    global fp
    depth_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_DEPTH_11BIT
    video_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_VIDEO_RGB
    depth = functools.partial(save_frame, depth_type)
    video = functools.partial(save_frame, video_type)
    start_time = time.time()
    with open(path, 'w') as fp:
        freenect.runloop(depth=depth,
                         video=video,
                         body=update_tilt)
    fps_rgb = total_frames_rgb / (time.time() - start_time)
    fps_depth = total_frames_depth / (time.time() - start_time)
    print('# frames(RGB): %d FPS(RGB): %f' % (total_frames_rgb,
                                              fps_rgb))
    print('# frames(DEPTH): %d FPS(DEPTH): %f' % (total_frames_depth,
                                                  fps_depth))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main(cmdparse.path(__doc__))

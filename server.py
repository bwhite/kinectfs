import freenect
import functools
import zmq
import time
import kinectfs_pb2


def send_frame(socket, frame_type, dev, data, timestamp):
    m = kinectfs_pb2.KinectMessage()
    f = m.frame
    try:
        f.height, f.width, f.channels = data.shape[:3]
    except ValueError:
        (f.height, f.width), f.channels = data.shape[:2], 1
    f.data, f.type = data.tostring(), frame_type
    f.timestamp, f.wall_time = timestamp, time.time()
    socket.send(m.SerializeToString())


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.HWM, 10)
    socket.bind("tcp://127.0.0.1:5000")
    depth_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_DEPTH_11BIT
    video_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_VIDEO_RGB
    depth = functools.partial(send_frame, socket, depth_type)
    video = functools.partial(send_frame, socket, video_type)
    freenect.runloop(depth=depth,
                     video=video)

if __name__ == '__main__':
    main()

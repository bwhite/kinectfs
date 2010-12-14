import freenect
import functools
import zmq


def send_frame(socket, frame_type, dev, data, timestamp):
    socket.send_pyobj((frame_type, data, timestamp))


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.HWM, 10)
    socket.bind("tcp://127.0.0.1:5000")
    depth = functools.partial(send_frame, socket, 'depth')
    video = functools.partial(send_frame, socket, 'video')
    freenect.runloop(depth=depth,
                     video=video)

if __name__ == '__main__':
    main()

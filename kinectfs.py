#!/usr/bin/env python
"""FUSE filesystem for mounting Kinect dumps made with client_record.py

The filesystem is read-only and as lazy as possible (creates files on the fly).
"""
import fuse
import stat
import errno
import os
import numpy as np
import kinectfs_pb2
import json

depth_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_DEPTH_11BIT
video_type = kinectfs_pb2.KinectMessage.KinectFrame.FREENECT_VIDEO_RGB
dump_path = '/mnt/ext/out.kdump'
fuse.fuse_python_api = (0, 2)


class KinectFS(fuse.Fuse):
    def __init__(self, *args, **kw):
        self._dump_path = dump_path
        self._build_index()
        fuse.Fuse.__init__(self, *args, **kw)

    def _mk_video_fn(self):
        return '%.10d.ppm' % len(self._video_index)

    def _mk_depth_fn(self):
        return '%.10d.pgm' % len(self._depth_index)

    def _mk_tilt_fn(self):
        return '%.10d.js' % len(self._tilt_index)

    def _parse_offset(self, offset):
        with open(self._dump_path) as fp:
            fp.seek(offset)
            sz = np.fromstring(fp.read(4), dtype=np.uint32)[0]
            return kinectfs_pb2.KinectMessage.FromString(fp.read(sz))

    def _video_read(self, offset):
        m = self._parse_offset(offset)
        return  'P6 %d %d 255\n%s' % (m.frame.width,
                                      m.frame.height,
                                      m.frame.data)

    def _depth_read(self, offset):
        m = self._parse_offset(offset)
        return  'P5 %d %d 65535\n%s' % (m.frame.width,
                                        m.frame.height,
                                        m.frame.data)

    def __tilt_read(self, m):
        out = {'accelerometer_x': m.tilt_state.accelerometer_x,
               'accelerometer_y': m.tilt_state.accelerometer_y,
               'accelerometer_z': m.tilt_state.accelerometer_z,
               'tilt_angle': m.tilt_state.tilt_angle,
               'tilt_status': m.tilt_state.tilt_status,
               'wall_time': m.tilt_state.wall_time}
        return json.dumps(out)

    def _tilt_read(self, offset):
        return self.__tilt_read(self._parse_offset(offset))

    def _read(self, index, offset):
        if index == self._tilt_index:
            return self._tilt_read(offset)
        elif index == self._video_index:
            return self._video_read(offset)
        elif index == self._depth_index:
            return self._depth_read(offset)
        else:
            raise TypeError('Unrecognized index type')

    def _video_bytes(self, m):
        sz = len('P6 %d %d 255\n' % (m.frame.width,
                                     m.frame.height))
        return sz + len(m.frame.data)

    def _depth_bytes(self, m):
        sz = len('P5 %d %d 65535\n' % (m.frame.width,
                                       m.frame.height))
        return sz + len(m.frame.data)

    def _tilt_bytes(self, m):
        return len(self.__tilt_read(m))

    def _build_index(self):
        self._tilt_index = {}
        self._video_index = {}
        self._depth_index = {}
        offset = 0
        with open(self._dump_path) as fp:
            while True:
                try:
                    sz = np.fromstring(fp.read(4), dtype=np.uint32)[0]
                except IndexError:
                    break
                m = kinectfs_pb2.KinectMessage.FromString(fp.read(sz))
                i = self._mk_tilt_fn()
                self._tilt_index[i] = (offset, self._tilt_bytes(m))
                if m.frame.type == video_type:
                    i = self._mk_video_fn()
                    self._video_index[i] = (offset, self._video_bytes(m))
                elif m.frame.type == depth_type:
                    i = self._mk_depth_fn()
                    self._depth_index[i] = (offset, self._depth_bytes(m))
                else:
                    print('Warning: Unsupported type [%s]' % (m.frame.type))
                offset += sz + 4
        tilt_pre = '/tilt/'
        depth_pre = '/depth/'
        video_pre = '/video/'
        tilt_f = lambda x: (tilt_pre + x, (self._tilt_index, tilt_pre))
        depth_f = lambda x: (depth_pre + x, (self._depth_index, depth_pre))
        video_f = lambda x: (video_pre + x, (self._video_index, video_pre))
        self._valid_files = {}
        self._valid_files.update(dict(map(tilt_f, self._tilt_index)))
        self._valid_files.update(dict(map(depth_f, self._depth_index)))
        self._valid_files.update(dict(map(video_f, self._video_index)))

    def getattr(self, path):
        st = fuse.Stat()
        if path in '/ /depth /video /tilt'.split():
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path in self._valid_files:
            index, prefix = self._valid_files[path]
            rel_path = path[len(prefix):]
            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1
            st.st_size = index[rel_path][1]
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        if path == '/':
            return [fuse.Direntry(f) for f in '. .. depth video tilt'.split()]
        elif path == '/depth':
            return [fuse.Direntry(f)
                    for f in '. ..'.split() + self._depth_index.keys()]
        elif path == '/video':
            return [fuse.Direntry(f)
                    for f in '. ..'.split() + self._video_index.keys()]
        elif path == '/tilt':
            return [fuse.Direntry(f)
                    for f in '. ..'.split() + self._tilt_index.keys()]
        else:
            return -errno.ENOENT

    def open(self, path, flags):
        print("Open[%s]" % path)
        if path not in self._valid_files:
            return -errno.ENOENT
        if not (flags & 3) == os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, length, offset):
        try:
            index, prefix = self._valid_files[path]
            rel_path = path[len(prefix):]
            return self._read(index, index[rel_path][0])[offset:offset + length]
        except KeyError:
            return -errno.ENOENT

if __name__ == "__main__":
    fs = KinectFS()
    fs.parse()
    fs.main()

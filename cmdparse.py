"""Command line parsing operations"""
import argparse


def _add_address(parser):
    parser.add_argument('--address', type=str,
                        help='Server listening address (default: 127.0.0.1)',
                        default='127.0.0.1')


def _add_port(parser):
    parser.add_argument('--port', type=int,
                        help='Server port (default: 10123)',
                        default='10123')


def _add_file(parser):
    parser.add_argument('--file', type=str,
                        help='Kinect recording path (default: default.kdump)',
                        default='default.kdump')


def address_port(doc):
    parser = argparse.ArgumentParser(description=doc)
    _add_address(parser)
    _add_port(parser)
    args = parser.parse_args()
    return args.address, args.port


def address_port_path(doc):
    parser = argparse.ArgumentParser(description=doc)
    _add_address(parser)
    _add_port(parser)
    _add_file(parser)
    args = parser.parse_args()
    return args.address, args.port, args.file


def path(doc):
    parser = argparse.ArgumentParser(description=doc)
    _add_file(parser)
    args = parser.parse_args()
    return args.file

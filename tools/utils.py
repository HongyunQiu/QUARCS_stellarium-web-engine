#!/usr/bin/python
# coding: utf-8

# Stellarium Web Engine - Copyright (c) 2018 - Noctua Software Ltd
#
# This program is licensed under the terms of the GNU AGPL v3, or
# alternatively under a commercial licence.
#
# The terms of the AGPL v3 license can be found in the main directory of this
# repository.

# Some utils functions that can be used by the other scripts.

import functools
import gzip
import hashlib
import os
import requests
import struct
import sys

# Degrees to radians
DD2R = 1.745329251994329576923691e-2

# Radians to degrees
DR2D = 57.29577951308232087679815


# Make sure that all the scripts are run from the root dir.
if not os.path.relpath(__file__).startswith('tools/'):
    print 'Should be run from root directory'
    sys.exit(-1)


def ensure_dir(file_path):
    '''Create a directory for a path if it doesn't exists yet'''
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def download(url, md5=None, unpacked_md5=False):
    '''download a file into data-src and return a path to it'''
    filename = os.path.basename(url)
    outpath = 'data-src/{}'.format(filename)
    if not os.path.exists(outpath):
        ensure_dir(outpath)
        print("Download '{}'".format(url))
        r = requests.get(url)
        with open(outpath, 'wb') as out:
            out.write(r.content)
    if md5:
        assert hashlib.md5(open(outpath).read()).hexdigest() == md5
    if unpacked_md5:
        data_md5 = hashlib.md5(gzip.open(outpath).read()).hexdigest()
        assert data_md5 == unpacked_md5

    return outpath


def parse(line, start, end, type=float, default=None, required=False,
          conv=None):
    '''parse a part of a line'''
    line = line[start - 1:end].strip()
    if not line:
        assert not required
        return default
    ret = type(line)
    if conv is not None: ret *= conv
    return ret


def shuffle_bytes(data, size):
    assert len(data) % size == 0
    ret = ''
    for i in range(size):
        for j in range(len(data) / size):
            ret += data[j * size + i]
    return ret

def compute_dir_md5(path):
    """Compute the md5 of all the files and dir of a directory
       The computation takes into account both the files content and the
       directories and file names.
    """
    m = hashlib.md5()
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = sorted(dirnames)
        filenames[:] = sorted(filenames)
        for d in dirnames:
            m.update(d)
        for f in filenames:
            m.update(open(os.path.join(dirpath, f)).read())
    return m.hexdigest()


def generator(filename, md5):
    """Decorator that checks if a generated file is already up to date
       This can be used to cache data that is slow to generate.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper():
            path = os.path.join('data-src', filename)
            if not os.path.exists(path):
                print('Generating %s' % path)
                ensure_dir(path)
                func(path)
            current_md5 = hashlib.md5(open(path).read()).hexdigest()
            if  current_md5 != md5:
                print 'Md5 for file %s changed!' % filename
                print 'Current md5: %s' % current_md5
                print 'Expected   : %s' % md5
                raise ValueError
            return path
        return wrapper
    return decorator

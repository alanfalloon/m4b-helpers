#! /usr/bin/env python

"""%prog [audio files]

Create a chapters text file, suitable for using with 'mp4chaps -i',
that can be used as chapters text for an m4a or m4b file created by
concatenating all the input files together.

The track names come from the 'song title' metatdata in the m4a, or
from the filename if there is no title metadata.
"""
from subprocess import Popen, PIPE
import re
import sys
from itertools import izip, count
from os.path import basename, splitext

def create_chapters(m4afiles):
    tracks = list(get_all_tracks(m4afiles))
    maxtracknum = max(n for (_,n,_) in tracks)
    tracknumwidth = len(str(maxtracknum))
    return ''.join(track_lines(tracks,tracknumwidth))

def get_all_tracks(m4afiles):
    for (i,m4afile) in izip(count(),m4afiles):
        try:
            (duration,title) = get_m4a_metadata(m4afile)
            yield (duration,i,title)
        except ValueError, e:
            print >> sys.stderr, e.args[0]
            continue

def get_m4a_metadata(m4afile):
    mp4info = Popen(['mp4info',m4afile],stdout=PIPE,close_fds=True)
    metadata = mp4info.communicate()[0]
    duration = get_m4a_duration(metadata)
    title = get_m4a_title(metadata,m4afile)
    return (duration, title)

def get_m4a_duration(metadata):
    audiotracks = list(audiotrack_re.finditer(metadata))
    ntracks = len(audiotracks)
    if ntracks != 1:
        raise ValueError, "%s has %d audio tracks, expected 1" % (m4afile,ntracks)
    (audiotrack,) = audiotracks
    secs = audiotrack.group(1)
    return float(secs)
audiotrack_re = re.compile(
    r"""^[0-9]+[ \t]+audio[ \t]+.*[ \t]([0-9]+(?:\.[0-9]+)?) secs,.*$""",
    re.M)

def get_m4a_title(metadata,filename):
    titlematch = title_re.search(metadata)
    if titlematch is not None:
        return titlematch.group(1).strip()
    return splitext(basename(filename))[0]
title_re = re.compile(
    r"""^[ \t]*Name:(.*)$""",
    re.M)

def track_lines(tracks,tracknumwidth):
    starttime=0.0
    for (duration, tracknum, title) in tracks:
        yield "%s %0*d - %s\n" % (timestr(starttime),tracknumwidth,tracknum,title)
        starttime += duration

def timestr(s):
    h = int(s / 3600)
    s -= h * 3600
    m = int(s / 60)
    s -= m * 60
    return "%02d:%02d:%06.3f" % (h,m,s)

if __name__ == "__main__":
    from optparse import OptionParser
    optp = OptionParser(usage=__doc__,version="%prog 0.1")
    opts, args = optp.parse_args()
    sys.stdout.write(create_chapters(args))

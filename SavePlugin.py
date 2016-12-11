#https://github.com/Stebalien/misc/blob/master/pithos-save.py
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
### BEGIN LICENSE
# Copyright (C) 2010 Kevin Mehall <km@kevinmehall.net>
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from pithos.plugin import PithosPlugin
from mutagen.mp4 import MP4
import os
from shutil import copyfile as copy
import urllib
import eyed3
import eyed3.id3

class SavePlugin(PithosPlugin):
    preference = 'save'
    _MUSIC_DIR = os.getenv("XDG_MUSIC_DIR") or os.path.expanduser("~/Music")

    def on_enable(self):
        self.song_rating_changed_handle = self.window.connect('song-changed', self.song_changed)

    def song_changed(self, window,  song):
        if song.rating and song.rating_str == 'love':
            path = os.path.join(SavePlugin._MUSIC_DIR, song.artist, song.album)
            filename = "%s.m4a" % song.title
            fullpath = os.path.join(path, filename)
            if os.path.exists(fullpath):
                return
            if not os.path.isdir(path):
                os.makedirs(path)
            #fetch = urllib.request.URLopen()
            #fetch.retrieve(song.audioUrl, fullpath)
            with urllib.request.urlopen(song.audioUrl) as response, open(fullpath, 'wb') as out_file:
                data = response.read() # a `bytes` object
                out_file.write(data)
            try:
                mp4file = MP4(fullpath)
                mp4file["\xa9nam"] = str(song.titlei, 'utf-8')
                mp4file["\xc2\xa9na"] = str(song.title, 'utf-8')
                mp4file["\xa9ART"] = str(song.artist, 'utf-8')
                mp4file["\xa9alb"] = str(song.album, 'utf-8')
                mp4file.save()
            except:
                audiofile = eyed3.load(fullpath)
                if audiofile.tag is None:
                    audiofile.tag = eyed3.id3.Tag()
                    audiofile.tag.file_info = eyed3.id3.FileInfo(fullpath)
                audiofile.tag.artist = u"" + song.artist
                audiofile.tag.album = u"" + song.album
                audiofile.tag.title = u"" + song.title
                audiofile.tag.save()
    def on_disable(self):
        self.window.disconnect(self.song_rating_changed_handle)

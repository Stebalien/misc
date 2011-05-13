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
from pithos.pithosconfig import get_data_file
from mutagen.mp4 import MP4
import os
from shutil import copyfile as copy
from glob import glob

class SavePlugin(PithosPlugin):
    preference = 'save'

    def on_enable(self):
        self.song_rating_changed_handle = self.window.connect('song-rating-changed', self.song_rating_changed)
        
    def song_rating_changed(self, window,  song):
        if song.rating and song.rating_str == 'love':
            tmp_files = glob("/tmp/pithos-??????")
            if not tmp_files:
                return
            src_file = tmp_files[-1]
            BASE="/home/steb/Media/Music"
            path = os.path.join(BASE, song.artist, song.album)
            filename = "%s.m4a" % song.title
            fullpath = os.path.join(path, filename)
            if os.path.exists(fullpath):
                return
            if not os.path.isdir(path):
                os.makedirs(path)
            copy(src_file, fullpath)
            mp4file = MP4(fullpath)
            mp4file["\xa9nam"] = unicode(song.title)
            mp4file["\xc2\xa9na"] = unicode(song.title)
            mp4file["\xa9ART"] = unicode(song.artist)
            mp4file["\xa9alb"] = unicode(song.album)
            mp4file.save()
            
    def on_disable(self):
        self.window.disconnect(self.song_rating_changed_handle)

#!/usr/bin/python2
"""
Look up words on the command line or based on selected text
and display their definitions.
"""
import subprocess

def lookup(*words):
    """
    Look up words in WordNet and return a generator of tuples of
    the words, their parts of speech, and their definitions.
    """
    for word in words:
        cmd = [
            '/usr/bin/wn', 
            word, 
            '-synsn', 
            '-synsv', 
            '-synsa', 
            '-synsr', 
            '-g', 
            '-n1'
        ]
        wordnet = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        out = wordnet.communicate()[0].splitlines()
        if len(out) > 1:
            partofspeech = out[1].split(' ')[-2]
            definition = out[4].split('-- (', 1)[1].split(';', 1)[0] + '.'
        else:
            partofspeech = "err"
            definition = "word not found."
        yield word.capitalize(), partofspeech, definition.capitalize()


if __name__ == "__main__":
    def _cli():
        """
        Get word(s) from the cmd arguments. Output to console.
        """
        for item in lookup(*sys.argv[1:]):
            print('[1;37m{}:  [0;32m{}. [0;36m{}[0m'.format(*item))

    def _gui():
        """
        Get word(s) from clipboard. Output to a notification bubble.
        """
        import gtk
        import pynotify
        if not pynotify.init("Dictionary"):
            return
        clipboard = gtk.Clipboard(selection="PRIMARY")
        if clipboard.wait_is_text_available():
            for item in lookup(*clipboard.wait_for_text().split()):
                title = item[0]
                body = "%s. %s" % (item[1], item[2])
                notification = pynotify.Notification(title, body)
                notification.show()
    import sys
    if sys.argv[1:]:
        _cli()
    else:
        _gui()

#!/usr/bin/python3
"""
Look up words on the command line or based on selected text
and display their definitions.
"""
import subprocess

__all__ = ("lookup",)

BIN='/usr/bin/wn'
CMD_ARGS = [
    '-synsn', 
    '-synsv', 
    '-synsa', 
    '-synsr', 
    '-g', 
    '-n1'
]

DEFAULT_FORMAT = '[1;37m{word}: [0;32m{part}. [0;36m{def}[0m'

def lookup(word):
    """
    Look up words in WordNet and return a generator of tuples of
    the words, their parts of speech, and their definitions.
    """
    cmd = [BIN, word]
    cmd.extend(CMD_ARGS)
    wn = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
    out = wn.communicate()[0].decode('utf8').splitlines()

    defn = None

    if len(out) > 1:
        partofspeech = out[1].split(' ')[-2]
        definition = out[4].split('-- (', 1)[1].split(';', 1)[0] + '.'
        defn = {"word": word, "part": partofspeech, "def": definition}

    return defn


def main(words=[], fmt=DEFAULT_FORMAT, command=None):
    import shlex
    """
    Get word(s) from the cmd arguments. Output to console.
    """
    defns = ((w, lookup(w)) for w in words)

    if command:
        cmd = shlex.split(command)
        for word, defn in defns:
            if defn:
                subprocess.call([a.format(**defn) for a in cmd], shell=False)
    else:
        for word, defn in defns:
            if defn:
                print(fmt.format(**defn))
            else:
                print("error: '{}' not found".format(word))

def parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-f", "--format",
                       dest="fmt",
                       metavar="FORMAT",
                       default=DEFAULT_FORMAT,
                       help="print format")

    group.add_argument("-e", "--exec",
                       dest="command",
                       help="run command instead of printing")

    parser.add_argument("words",
                        metavar="word",
                        nargs='+',
                        help="word to define")

    return parser.parse_args()

if __name__ == "__main__":
    main(**vars(parse_args()))



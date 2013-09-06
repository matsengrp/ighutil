import bz2
import gzip
import contextlib
import functools
import os.path
import shutil
import sys
import tempfile

# From https://github.com/lh3/readfq
def readfq(fp): # this is a generator function
    last = None # this is a buffer keeping the last unprocessed line
    while True: # mimic closure; is it a bad idea?
        if not last: # the first record or a record following a fastq
            for l in fp: # search for the start of the next record
                if l[0] in '>@': # fasta/q header line
                    last = l[:-1] # save this line
                    break
        if not last: break
        name, seqs, last = last[1:], [], None
        for l in fp: # read the sequence
            if l[0] in '@+>':
                last = l[:-1]
                break
            seqs.append(l[:-1])
        if not last or last[0] != '+': # this is a fasta record
            yield name, ''.join(seqs), None # yield a fasta record
            if not last: break
        else: # this is a fastq record
            seq, leng, seqs = ''.join(seqs), 0, []
            for l in fp: # read the quality
                seqs.append(l[:-1])
                leng += len(l) - 1
                if leng >= len(seq): # have read enough quality
                    last = None
                    yield name, seq, ''.join(seqs); # yield a fastq record
                    break
            if last: # reach EOF before reading enough quality
                yield name, seq, None # yield a fasta record instead
                break


@contextlib.contextmanager
def tempdir(**kwargs):
    td = tempfile.mkdtemp(**kwargs)
    try:
        yield functools.partial(os.path.join, td)
    finally:
        shutil.rmtree(td)

def opener(mode, *args, **kwargs):
    """
    Open a file, with optional compression based on extension
    """
    exts = {'.bz2': bz2.BZ2File,
            '.gz': gzip.open}
    def open_file(path):
        if path == '-':
            if mode.startswith('r'):
                return sys.stdin
            else:
                return sys.stdout

        open_fn = exts.get(os.path.splitext(path)[1], open)
        return open_fn(path, mode, *args, **kwargs)
    return open_file
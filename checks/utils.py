import os
from stat import *

class TailFile(object):

    def __init__(self,logger,path,callback):
        self._path = path
        self._f = None
        self._inode = None
        self._size = 0
        self._log = logger
        self._callback = callback

    def _open_file(self,move_end=False,where=False):

        already_open = False
        #close and reopen to handle logrotate
        if self._f is not None:
            self._f.close()
            self._f = None
            already_open = True

        stat = os.stat(self._path)
        inode = stat[ST_INO]
        size = stat[ST_SIZE]

        if already_open:
            if self._inode is not None:
                #Check if file has been removed
                if inode != self._inode:
                    self._log.debug("File removed, reopening")
                    move_end = False
                    where = False
            elif self._size > 0:
                #Check if file has been truncated
                if size < self._size:
                    self._log.debug("File truncated, reopening")
                    move_end = False
                    where = False

        self._inode = inode
        self._size = size

        self._f = open(self._path,'r')
        if move_end:
            self._f.seek(1,os.SEEK_END)
        elif where:
            self._log.debug("Reopening file at {0}".format(where))
            self._f.seek(where)

        return True

    def tail(self,move_end=True):

        try:
            self._open_file(move_end=move_end)

            done = False
            while True:
                if done:
                    break

                where = self._f.tell()
                line = self._f.readline()
                if line:
                   done = self._callback(line.rstrip("\n"))
                else:
                    yield True
                    self._open_file(move_end=False,where=where)
        except Exception, e:
            # log but survive
            self._log.exception(e)
            raise StopIteration(e)


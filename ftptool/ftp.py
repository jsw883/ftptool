"""
FTP wrappers for :class:`ftplib` implementing a slightly more usable API.
"""

import ftplib
import os

from functools import partial  # required


# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------

def parse_dir_listing(
        line, dirs=[], files=[], links=[], pipes=[], sockets=[], devices=[]):
    """Parses output from :code:`ls -al` and :meth:`ftplib.FTP.dir`.

    Args:
        line (str): output from :code:`ls -al` and :meth:`ftplib.FTP.dir`
        **kwargs (dict): dictionary of lists to which to append, where keys
            are a subset of 'dirs', 'files', 'links', 'pipes', 'sockets',
            or 'devices'

    This is intended to be used with :func:`functools.partial`, where you
    first create a dictionary with the desired subset of file types or modes
    to track, and then create a partial function by unpacking the dictionary
    as named arguments to :func:`parse_dir_listing`, leaving :code:`line`
    unspecified.

    Solaris specific doors, identified by 'D', are ignored.

    Example::

        l = '-rw-r-----    1 user     user            5 May 23 07:00 file.py'
        d = 'drw-r-----    1 user     user            5 May 23 07:00 dir/'

        k = dict(dirs=[], files=[])
        p = partial(parse, **k)

        p(l)
        p(d)

        print(k)

    """

    mode, _, _, _, _, _, _, _, name = line.split()

    if mode.startswith('d'):
        dirs.append(name)
    elif mode.startswith('-'):
        files.append(name)
    elif mode.startswith('l'):
        links.append(name)
    elif mode.startswith('p'):
        pipes.append(name)
    elif mode.startswith('s'):
        sockets.append(name)
    elif mode.startswith('c') or mode.startswith('b'):
        devices.append(name)
    else:
        raise ValueError('Line type "{}" not recognized'.format(line[:1]))


# -----------------------------------------------------------------------------
# FTP
# -----------------------------------------------------------------------------

class FTP(object):
    """Wrapper for :class:`ftplib.FTP` implementing a slightly more usable API.
    """

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------

    def __init__(self, host, username='anonymous', password='', timeout=None):
        """Connects to an FTP server, returning a new instance of :class:`FTP`.

        Follows the same default behaviour as :class:`ftplib.FTP`.

        Args:
            host (str): hostname (exluding port number)
            username (str): username
            password (str): password
            timeout (int): timeout (seconds)
        """

        self.ftp = ftplib.FTP(
            host=host, user=username, passwd=password, timeout=timeout)

    def __str__(self):
        """String representation for an instance of :class:`FTP`.
        """

        return "<%s at %s:%d (%s)>" % (
            self.__class__.__name__, self.ftp.host, self.ftp.port, self.ftp)

    def quit(self):
        """Send quit command (politely).
        """

        self.ftp.quit()

    def close(self):
        """Send close command.
        """

        self.ftp.close()

    # -------------------------------------------------------------------------
    # Traverse
    # -------------------------------------------------------------------------

    @property
    def current_directory(self):
        """Current directory.

        Defined using the :class:`Property` decorator as the current directory
        is managed by :meth:`ftplib.FTP.pwd` and :meth:`ftplib.FTP.cwd` to
        ensure synchronization with the remote server.
        """
        return self.ftp.pwd()

    @current_directory.setter
    def current_directory(self, directory):
        self.ftp.cwd(directory)

    def get_remaining_directory(self, directory):
        """Navigates to the deepest existing directory in the path specified.

        Args:
            directory (str): remote directory

        Returns:
            str: remaining directories relative to deepest existing directory
        """

        def recurse(directory):
            try:
                self.current_directory = directory
                return ''
            except ftplib.Error:
                head, trailing = os.path.split(directory)
                name = recurse(head)
                return os.path.join(name, trailing).rstrip('/')

        current_directory = self.current_directory
        remaining = recurse(directory)
        self.current_directory = current_directory

        return remaining

    def dir(self, directory):
        """Returns remote directory listing.

        Args:
            directory (str): remote directory

        Returns:
            tuple: tuple containing a list of directories and a list of files
                found in the current directory
        """

        d = dict(dirs=[], files=[])
        p = partial(parse_dir_listing, **d)

        self.ftp.dir(directory, p)

        return tuple([d['dirs'], d['files']])

    def walk(self, directory, topdown=True, onerror=None, followlinks=False):
        """Generates the file names in a directory tree by walking dynamically.

        Args:
            directory (str): remote directory
            topdown (bool): generate tuples before recursing into subdirectory
            onerror (function): callback for explicit error handling (optional)
            followlinks (bool): recurse into symbolic links

        Yields:
            tuple: tuple containing current directory, a list of directories,
                and a list of files found in the current directory

        Emmulates :func:`os.walk` but for FTP, with the same functionality and
        error handling (backed by the appropriate :class:`ftplib:FTP` methods).
        """

        # Get directory listing
        try:
            d = self.dir(directory)
        except Exception as err:
            if onerror is not None:
                onerror(err)
            return

        # Return first if topdown is enabled
        if topdown:
            yield directory, d[0], d[1]

        # Walk directory listing recursively
        for name in d[0]:
            subdirectory = os.path.join(directory, name)
            if followlinks or not os.path.islink(subdirectory):
                for x in self.walk(
                        subdirectory, topdown, onerror, followlinks):
                    yield x

        # Return first if topdown is disabled
        if not topdown:
            yield top, d[0], d[1]

    # -------------------------------------------------------------------------
    # Make
    # -------------------------------------------------------------------------

    def get_file_proxy(self, filename):
        """Creates a new instance of :class:`FTPFileProxy`.

        Args:
            filename (str): filename relative to the current directory
        """
        return FTPFileProxy(
            self.ftp, os.path.join(self.current_directory, filename))

    def mkdir(self, directory):
        """Makes remote directory.

        Args:
            directory (str): remote directory
        """

        self.ftp.mkd(directory)

    def rmdir(self, directory):
        """Removes remote directory.

        Args:
            directory (str): remote directory
        """

        self.ftp.rmd(directory)

    def makedirs(self, directory):
        """Makes remote directories recursively.

        Args:
            directory (str): remote directory to be created
        """

        remaining = os.path.split(self.get_remaining_directory(directory))

        if remaining:

            for name in remaining:
                directory = os.path.dirname(directory)

            for name in remaining:
                directory = os.path.join(directory, name)
                try:
                    self.mkdir(directory)
                except ftplib.Error:
                    pass

    # -------------------------------------------------------------------------
    # Transfer
    # -------------------------------------------------------------------------

    def download_directory(
            self, server_directory, local_directory, automkdir=True):
        """Copy contents of server directory to local directory.

        Args:
            server_directory (str): server directory
            local_directory (str): local directory
        """

        if automkdir:
            os.makedirs(local_directory)

        for source_directory, dirs, files in self.walk(server_directory):

            target_directory = os.path.join(
                local_directory,
                source_directory[len(server_directory):].lstrip('/'))

            for name in dirs:
                name = os.path.join(target_directory, name)
                if not os.path.exists(name):
                    os.mkdir(name)

            for name in files:
                target_name = os.path.join(target_directory, name)
                source_name = os.path.join(source_directory, name)
                self.get_file_proxy(source_name).filename_download(target_name)

    def upload_directory(
            self, local_directory, server_directory, automkdir=True):
        """Copy contents of local directory to server directory.

        Args:
            server_directory (str): server directory
            local_directory (str): local directory
        """

        if automkdir:
            os.makedirs(local_directory)

        for source_directory, dirs, files in os.walk(local_directory):

            target_directory = os.path.join(
                server_directory,
                source_directory[len(local_directory):].lstrip('/'))

            for name in dirs:
                name = os.path.join(target_directory, name)
                try:
                    self.mkdir(name)
                except ftplib.Error:
                    pass

            for name in files:
                target_name = os.path.join(target_directory, name)
                source_name = os.path.join(source_directory, name)
                self.get_file_proxy(target_name).filename_upload(source_name)


# -----------------------------------------------------------------------------
# FTPFileProxy
# -----------------------------------------------------------------------------

class FTPFileProxy(object):
    """Class for manipulating a file on a remote FTP server.
    """

    # -------------------------------------------------------------------------
    # Config
    # -------------------------------------------------------------------------

    def __init__(self, ftp, filename):
        """Returns a new instance of :class:`FTPFileProxy`.

        Args:
            ftp (FTP): :class:`FTP` object for remote server functionality
            filename (str): remote filename relative to current directory
        """
        self.ftp = ftp
        self.filename = filename

    # -------------------------------------------------------------------------
    # Upload
    # -------------------------------------------------------------------------

    def upload(self, f):
        """Upload from a local *file object* f (opened in binary mode).

        Args:
            f (file object): file object (opened in binary read mode)
        """
        self.ftp.storbinary("STOR {}".format(self.filename), f)

    def filename_upload(self, filename):
        """Upload from a local file specified by filename (to be opened).

        Args:
            filename (str): local filename (can be absolute or relative)
        """
        with open(filename, 'rb') as f:
            self.upload(f)

    # -------------------------------------------------------------------------
    # Download
    # -------------------------------------------------------------------------

    def download(self, f):
        """Downlaod to a local *file object* f (opened in binary mode).

        Args:
            f (file object): file object (opened in binary write mode)
        """
        self.ftp.retrbinary("RETR {}".format(self.filename), f.write)

    def filename_download(self, filename):
        """Download to a local file specified by filename (to be opened).

        Args:
            filename (str): local filename (can be absolute or relative)
        """
        with open(filename, 'wb') as f:
            self.download(f)

    # -------------------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------------------

    def delete(self):
        """Delete remote file permanently.
        """
        self.ftp.delete(self.filename)

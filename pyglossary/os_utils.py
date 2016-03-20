import os
import shutil

class indir:
    """
    mkdir + chdir shortcut to use with `with` statement.

        >>> print(os.getcwd())  # -> "~/projects"
        >>> with indir('my_directory', create=True):
        >>>     print(os.getcwd())  # -> "~/projects/my_directory"
        >>>     # do some work inside new 'my_directory'...
        >>> print(os.getcwd())  # -> "~/projects"
        >>> # automatically return to previous directory.
    """
    def __init__(self, directory, create=False, clear=False):
        self.oldpwd = None
        self.dir = directory
        self.create = create
        self.clear = clear

    def __enter__(self):
        self.oldpwd = os.getcwd()
        if os.path.exists(self.dir):
            if self.clear:
                shutil.rmtree(self.dir)
                os.makedirs(self.dir)
        elif self.create:
            os.makedirs(self.dir)
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.oldpwd)
        self.oldpwd = None

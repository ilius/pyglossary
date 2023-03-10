"""
Interface base class implementations.
taken from https://github.com/mrogaski/pygopher-interfaces

MIT License

Copyright (c) 2021 Mark Rogaski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import inspect
import sys
import typing as tp

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

__version__ = version("pygopher-interfaces")


def method_signatures(obj: type) -> tp.Set[inspect.Signature]:
    """
    Return the set of public method signatures for a class.

    Args:
        obj: a class

    Returns:
        A set containing the method signatures.  Dunder methods,
        private methods, and properties are excluded.

    """
    return {
        inspect.signature(attribute)
        for attribute in [
            getattr(obj, name)
            for name in dir(obj) if not name.startswith("_")
        ]
        if callable(attribute)
    }


class Interface(type):
    """
    Metaclass that defines the subclass relationship without inheritance.
    """

    def __subclasscheck__(self, subclass: type) -> bool:
        """

        Args:
            subclass: a class which will be checked for matching method signatures.

        Returns:
            True if the subclass implements the interface, false otherwise.

        """

        interface_methods = method_signatures(self)
        class_methods = method_signatures(subclass)
        return interface_methods.issubset(class_methods)

    def __instancecheck__(self, instance: type) -> bool:
        """

        Args:
            instance: an object which will be checked for matching method signatures.

        Returns:
            True if the instance class implements the interface, false otherwise.

        """
        return issubclass(type(instance), self)

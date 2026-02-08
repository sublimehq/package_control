# Package Control

The [Sublime Text](http://www.sublimetext.com) package manager. 
It allows users to find, install and keep packages up to date.

## Installation

### Sublime Text Installer Tool

The easiest way to install is ...

1. Open `Command Palette` using <kbd>ctrl+shift+P</kbd> or menu item `Tools → Command Palette...`
2. Choose `Install Package Control`
3. Hit <kbd>Enter</kbd>

> [!WARNING]
>
> Package Control 3.4.1 is installed up to ST4200,
> which may fail loading on some modern OSs,
> if required OpenSSL 1.1.1 libraries are missing.
> 
> Please follow manual install steps, then.

### Manual Install

1. Open Sublime Text's console
2. paste and run the following script

```py
from urllib.request import urlretrieve;urlretrieve(url="https://download.sublimetext.com/Package%20Control.sublime-package", filename=sublime.installed_packages_path() + '/Package Control.sublime-package')
```

> [!NOTE]
>
> Package Control.sublime-package is exactly the same, 
> as downloaded by the installer.

## Usage

All of the primary features of Package Control are exposed through the command palette.

To install a package:

1. Open the command palette
2. Type "Install Package"
3. Select a package from the list

For more features, see https://packagecontrol.io/docs/usage
or https://docs.sublimetext.io/guide/package-control/usage.html.

## Documentation

The documentation for Package Control can be found at https://packagecontrol.io/docs
or community driven documentation at https://docs.sublimetext.io.

## Bug Reports

If you find a bug with Package Control, please follow the directions at https://packagecontrol.io/docs/issues to submit an issue.

## License

Package Control is licensed under the MIT license.

```
Copyright (c) 2011-2025 Will Bond <will@wbond.net>
Copyright (c) 2026 Sublime HQ Pty Ltd, Woollahra, Sydney.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

# microUrllib

A mini version of urllib for micropython without dependencies

It is derived by micropython's unix version of [urllib](https://github.com/micropython/micropython-lib/blob/master/unix-ffi/urllib.parse/urllib/parse.py) and for now it only supports:

- quote
- quote_from_bytes
- unquote
- unquote_to_bytes

More to be added if necessary/requested in the future.

# Installation

## Using `mip`

For network connected devices, call:

```py
import mip
mip.install("github:insighio/microUrllib")
```

## File Transfer

Download and transfer files in the board through [ampy](https://pypi.org/project/adafruit-ampy/).

A simple benchmarking tool.

## Benchmark Setup (Windows)

Traditionally, most Python versions have a global interpreter lock (GIL) which prevents
more than 1 thread to run at the same time. With 3.13, there are free-threaded versions
of Python which allow one to bypass this constraint. This section walks through how
to do that on Windows. Use PowerShell.

Based on: https://docs.python.org/3/using/windows.html#

Go to `Microsoft Store` and install `Python Install Manager` and follow the instructions
presented. You may have to make certain changes to alias used by your machine (that
should be guided by the installation process).

Based on: https://docs.python.org/3/whatsnew/3.13.html#free-threaded-cpython

In PowerShell, install the free-threaded version of Python of your choice. In this guide
we will install `3.14t`:

```bash
py install 3.14t
```

Then, set up and activate the virtual environment with:

```bash
python3.14t -m venv venv
. ./venv/Scripts/activate
pip install -r requirements.txt
```

To activate the virtual environment, use:

```bash
. ./venv/Scripts/activate
```

To deactivate it, you may use:

```bash
deactivate
```

## Complete Setup

Running these tests requires you to have the agent running in a separate process. You
may open a separate PowerShell window or VSCode window and run your agent there.
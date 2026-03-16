import asyncio
import shutil
import subprocess
import datetime

from pathlib import Path

from ._common import (
    create_agent_path,
    SDKVersion,
)
from ._common.utils import create_agent_path

async def main():

    script_path = Path(create_agent_path("quickstart", SDKVersion.PYTHON))

    runner = shutil.which("pwsh") or shutil.which("powershell")
    if runner is None:
        raise FileNotFoundError("Could not find pwsh or powershell in PATH")

    # proc = subprocess.Popen(
    #     [runner, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
    #     stdout=subprocess.PIPE,
    #     cwd=script_path.parent
    # )

    import io, sys
    filename = "test.log"
    with io.open(filename, "w", encoding="utf-8") as writer, io.open(filename, "rb", 128) as reader:
        process = subprocess.Popen(
            [runner, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            stdout=writer,
            stderr=writer,
            cwd=script_path.parent,
            shell=True,
        )
        while process.poll() is None:
            sys.stdout.write(reader.read().decode())
            await asyncio.sleep(0.5)

    # wait for the agent to start running
    # print("Waiting for agent to start...")

    process.terminate()

if __name__ == "__main__":
    asyncio.run(main())
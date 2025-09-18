# this will mock HTTP requests
import logging

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import ChannelAdapter

from extension_agent import APP, ext, MockAdapter

logger = logging.getLogger("src.extension.extension")
print(logger)
        
def main():

    while True:
        input(">>> Press Enter to send an activity...")
        await MockAdapter.send_activity()
        print("Activity sent.")

if __name__ == "__main__":
    main()
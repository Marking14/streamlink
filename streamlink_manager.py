import os
import streamlink
import shutil
import signal
import sys

class StreamlinkManager:
    def __init__(self, config):
        self.config = config

    M3U8_EXTENSIONS = ['m3u8']

    def cleanup(self, fd, temp_filename, final_filename, *args):
        """
        Cleanup function to close the file descriptor and move the temporary file
        to its final destination.
        """
        fd.close()
        if os.path.exists(temp_filename):
            shutil.move(temp_filename, final_filename)

    def run_streamlink(self, user, recorded_filename):
        session = streamlink.Streamlink()
        session.set_option("twitch-disable-hosting", True)
        session.set_option("twitch-disable-ads", True)
        session.set_option("retry-max", 5)
        session.set_option("retry-streams", 60)

        if self.config.oauth_token:
            session.set_option("http-headers", f"Authorization=OAuth {self.config.oauth_token}")
        quality = self.config.quality
        streams = session.streams(f"twitch.tv/{user}")
        if quality not in streams:
            quality = "best"
        stream = streams[quality]
        temp_filename = f"{recorded_filename}.part"
        final_filename = f"{recorded_filename}"
        
        # Open the stream
        fd = stream.open()

        # Register signal handlers for SIGTERM and SIGINT to ensure cleanup
        signal.signal(signal.SIGTERM, lambda *args: self.cleanup(fd, temp_filename, final_filename, *args))
        signal.signal(signal.SIGINT, lambda *args: self.cleanup(fd, temp_filename, final_filename, *args))

        try:
            with open(temp_filename, 'ab+') as f:
                while True:
                    data = fd.read(1024)
                    if not data:
                        break
                    f.write(data)
        finally:
            # Ensure cleanup is called when the try block exits
            self.cleanup(fd, temp_filename, final_filename)

import logging
import asyncio
import signal
import sys
import os
import platform
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import importlib
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotReloader(FileSystemEventHandler):
    def __init__(self, module_name='main'):
        self.module_name = module_name
        self.bot = None
        self.observer = Observer()
        self.should_reload = False
        self.last_reload = 0
        self.reload_cooldown = 1.0  # Minimum time between reloads in seconds
        
    async def start_bot(self):
        while True:
            try:
                # Import/reimport the bot module
                if self.module_name in sys.modules:
                    module = importlib.reload(sys.modules[self.module_name])
                else:
                    module = importlib.import_module(self.module_name)
                
                # Create new bot instance
                self.bot = module.create_bot()
                
                # Start file watching if not already started
                if not self.observer.is_alive():
                    self.observer.schedule(self, path=".", recursive=False)
                    self.observer.start()
                
                # Run bot
                await self.bot.start(module.TOKEN)
                
            except Exception as e:
                logger.error(f"Error in bot: {e}")
                await asyncio.sleep(5)  # Wait before retry
                
            finally:
                if self.bot:
                    try:
                        await self.bot.close()
                    except Exception as e:
                        logger.error(f"Error closing bot: {e}")
                
                if self.should_reload:
                    self.should_reload = False
                    logger.info("Restarting bot...")
                    continue
                break

    def on_modified(self, event):
        """Called when a file is modified"""
        # Windows sometimes triggers multiple events
        current_time = time.time()
        if current_time - self.last_reload < self.reload_cooldown:
            return

        if isinstance(event, FileModifiedEvent) and event.src_path.endswith('.py'):
            # Convert path to module name for comparison
            modified_module = os.path.basename(event.src_path)[:-3]  # Remove .py
            
            # Only reload for main.py changes to prevent double reloads
            if modified_module == "main":
                logger.info(f"Detected change in {event.src_path}")
                self.should_reload = True
                self.last_reload = current_time
                asyncio.create_task(self.safe_close())

    async def safe_close(self):
        """Safely close the bot with platform-specific handling"""
        if self.bot:
            try:
                await self.bot.close()
            except Exception as e:
                logger.error(f"Error during safe close: {e}")

def setup_signal_handlers(reloader):
    """Set up platform-specific signal handlers"""
    def signal_handler():
        logger.info("Shutting down...")
        reloader.observer.stop()
        if reloader.bot:
            asyncio.create_task(reloader.safe_close())

    if platform.system() == 'Windows':
        # Windows only supports SIGINT and SIGTERM
        signals = [signal.SIGINT, signal.SIGTERM]
    else:
        # Unix-like systems support more signals
        signals = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]

    loop = asyncio.get_event_loop()
    for sig in signals:
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Fallback for signals not supported on this platform
            signal.signal(sig, lambda s, f: signal_handler())

async def main():
    """Main function to run the bot with hot reload"""
    reloader = BotReloader()
    
    # Set up platform-specific signal handling
    setup_signal_handlers(reloader)
    
    try:
        await reloader.start_bot()
    finally:
        reloader.observer.stop()
        reloader.observer.join()
        logger.info("Bot reloader shutdown complete")

if __name__ == "__main__":
    if platform.system() == 'Windows':
        # Use WindowsSelectorEventLoopPolicy on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
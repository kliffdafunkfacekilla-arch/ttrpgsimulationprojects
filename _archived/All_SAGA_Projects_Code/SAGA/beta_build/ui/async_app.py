"""
Bootstrapper script for the S.A.G.A Engine Beta.
Initializes the Qt Application, the qasync Event Loop, and launches the Main Window.
"""
import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

from beta_build.ui.main_window import SagaDesktopApp

async def main():
    """
    Main asynchronous entry point.
    Merges the asyncio event loop with PyQt6's event loop via qasync.
    """
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    main_window = SagaDesktopApp()
    main_window.show()

    with loop:
        try:
            loop.run_forever()
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())

import logging

from app.utils.file_utils import app_dir


def setup_logging():
    try:
        (app_dir() / "config").mkdir(exist_ok=True)
        logging.basicConfig(
            filename=app_dir() / "config" / "ametista.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    except OSError:
        logging.basicConfig(level=logging.INFO)


def main():
    setup_logging()
    from app.core.converter_manager import ConverterManager
    from app.core.settings import Settings
    from app.ui.main_window import MainWindow

    MainWindow(ConverterManager(), Settings.load()).mainloop()


if __name__ == "__main__":
    main()

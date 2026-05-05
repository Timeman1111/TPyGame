import sounddevice as sd
import numpy as np

def play_sound(audio: np.ndarray , fs: int):
    sd.play(audio, fs)

class AudioInterface:
    """
    Represents an interface for interacting with audio devices.

    This class provides functionality to retrieve and manage a list of
    currently available audio devices. It ensures that the list of devices
    remains up-to-date and provides an easy way to access this information.
    """
    available_devices = sd.query_devices()
    def __init__(self):
        """
        Initializes an instance of the class.

        This constructor sets up the initial state of the instance by calling
        internal methods or performing any necessary setup tasks, such as
        initializing attributes or updating state.

        Raises:
            AnyTypeError: If an error occurs during initialization.
        """
        self.__update_available_devices()

    def __update_available_devices(self):
        """
        Updates the list of available audio devices and updates the class-level
        list of available devices.

        Raises:
            None

        Returns:
            bool: Always returns True indicating the update was successful.
        """
        devices = sd.query_devices()

        AudioInterface.available_devices = devices

        return True

    def get_devices(self):
        """
        Retrieves a list of currently available audio devices.

        This method updates the list of available audio devices and returns it.

        Returns:
            list:
                A list of available audio devices.
        """
        self.__update_available_devices()
        return AudioInterface.available_devices

if __name__ == "__main__":
    audioInterface = AudioInterface()

    for device in audioInterface.get_devices():
        print(device)


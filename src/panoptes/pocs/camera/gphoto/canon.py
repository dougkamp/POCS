from astropy import units as u
from panoptes.pocs.camera.gphoto.base import AbstractGPhotoCamera
from panoptes.utils import error
from panoptes.utils.time import current_time
from panoptes.utils.utils import get_quantity_value


class Camera(AbstractGPhotoCamera):

    def __init__(self, readout_time: float = 1.0, file_extension: str = 'cr2', connect: bool = True,
                 *args, **kwargs):
        """Create a camera object for a Canon EOS DSLR.

        Args:
            readout (float): The time it takes to read out the file from the
                camera, default 1.0 second.
            file_extension (str): The file extension to use, default `cr2`.
            connect (bool): Connect to camera on startup, default True.
        """
        kwargs['readout_time'] = readout_time
        kwargs['file_extension'] = file_extension
        super().__init__(*args, **kwargs)
        self.logger.debug("Creating Canon DSLR GPhoto2 camera")

        if connect:
            self.connect()

    @property
    def bit_depth(self):
        return 12 * u.bit

    @property
    def egain(self):
        return 1.5 * (u.electron / u.adu)

    def connect(self):
        """Connect to Canon DSLR.

        Gets the serial number from the camera and sets various settings.
        """
        self.logger.debug('Connecting to Canon gphoto2 camera')

        # Get serial number
        _serial_number = self.get_property('serialnumber')
        if not _serial_number:
            raise error.CameraNotFound(f"Camera not responding: {self}")

        self._serial_number = _serial_number

        # Properties to be set upon init.
        prop2index = {
            '/main/capturesettings/autoexposuremode': 3,  # 3 - Manual; 4 - Bulb
            '/main/capturesettings/drivemode': 0,  # Single exposure
            '/main/capturesettings/focusmode': 0,  # Manual (don't try to focus)
            '/main/imgsettings/imageformat': 9,  # RAW
            '/main/imgsettings/imageformatsd': 9,  # RAW
            '/main/settings/capturetarget': 0,  # Capture to RAM, for download
            '/main/settings/reviewtime': 0,  # Screen off after taking pictures
            '/main/imgsettings/iso': 1,  # ISO 100
            '/main/capturesettings/shutterspeed': 0,  # Bulb
        }

        owner_name = 'PANOPTES'
        artist_name = self.get_config('pan_id', default=owner_name)
        copy_right = f'{owner_name}_{current_time().datetime:%Y}'

        prop2value = {
            'artist': artist_name,
            'copyright': copy_right,
            'ownername': owner_name,
        }

        self.set_properties(prop2index=prop2index, prop2value=prop2value)

        # TODO check this works on all Canon models.
        self.model = self.get_property('d402')

        self._connected = True

    def _start_exposure(self,
                        seconds=None,
                        filename=None,
                        dark=False,
                        header=None,
                        iso=100,
                        *args, **kwargs):
        """Start the exposure.

        Tested With:
            * Canon EOS 100D

        Args:
            seconds (u.second, optional): Length of exposure.
            filename (str, optional): Image is saved to this filename.
            header (dict or Header, optional): The metadata to be added as FITS headers.
            iso (int, optional): The ISO setting to use for the exposure, default 100.
        """
        # Make sure we have just the value, no units
        seconds = get_quantity_value(seconds)

        shutterspeed_idx = self.get_shutterspeed_index(seconds=seconds, return_minimum=True)

        cmd_args = [
            f'--set-config', f'iso={iso}',
            f'--filename', f'{filename}',
            f'--set-config-index', f'shutterspeed={shutterspeed_idx}',
            f'--wait-event=1s',
        ]

        if shutterspeed_idx == 0:
            # Bulb setting.
            cmd_args.extend([
                f'--set-config-index', 'eosremoterelease=2',
                f'--wait-event={int(seconds):d}s',
                f'--set-config-index', 'eosremoterelease=4',
                f'--wait-event-and-download=2s',
            ])
        else:
            # Known shutterspeed value.
            cmd_args.extend([
                f'--capture-image-and-download',
            ])

        try:
            self.command(cmd_args)
        except error.InvalidCommand as e:
            self.logger.warning(e)
        else:
            readout_args = (filename, header)
            return readout_args

    @classmethod
    def get_shutterspeed_index(cls, seconds: float, return_minimum: bool = False):
        """Looks up the appropriate shutterspeed setting for the given seconds.

        If the given seconds does not match a set shutterspeed, the 'bulb' setting
        is returned.
        """
        seconds = get_quantity_value(seconds, unit='second')
        # TODO derive these from `load_properties`.
        # The index corresponds to what gphoto2 expects.
        shutter_speeds = {
            "bulb": "bulb",
            "30": 30,
            "25": 25,
            "20": 20,
            "15": 15,
            "13": 13,
            "10.3": 10.3,
            "8": 8,
            "6.3": 6.3,
            "5": 5,
            "4": 4,
            "3.2": 3.2,
            "2.5": 2.5,
            "2": 2,
            "1.6": 1.6,
            "1.3": 1.3,
            "1": 1,
            "0.8": 0.8,
            "0.6": 0.6,
            "0.5": 0.5,
            "0.4": 0.4,
            "0.3": 0.3,
            "1/4": 1 / 4,
            "1/5": 1 / 5,
            "1/6": 1 / 6,
            "1/8": 1 / 8,
            "1/10": 1 / 10,
            "1/13": 1 / 13,
            "1/15": 1 / 15,
            "1/20": 1 / 20,
            "1/25": 1 / 25,
            "1/30": 1 / 30,
            "1/40": 1 / 40,
            "1/50": 1 / 50,
            "1/60": 1 / 60,
            "1/80": 1 / 80,
            "1/100": 1 / 100,
            "1/125": 1 / 125,
            "1/160": 1 / 160,
            "1/200": 1 / 200,
            "1/250": 1 / 250,
            "1/320": 1 / 320,
            "1/400": 1 / 400,
            "1/500": 1 / 500,
            "1/640": 1 / 640,
            "1/800": 1 / 800,
            "1/1000": 1 / 1000,
            "1/1250": 1 / 1250,
            "1/1600": 1 / 1600,
            "1/2000": 1 / 2000,
            "1/2500": 1 / 2500,
            "1/3200": 1 / 3200,
            "1/4000": 1 / 4000,
        }

        try:
            # First check by key.
            return list(shutter_speeds.keys()).index(seconds)
        except ValueError:
            # Then check by value.
            try:
                # Check minimum of everything after 'bulb'.
                if return_minimum and seconds < min(list(shutter_speeds.values())[1:]):
                    return len(shutter_speeds) - 1
                else:
                    return list(shutter_speeds.values()).index(seconds)
            except ValueError:
                return 0

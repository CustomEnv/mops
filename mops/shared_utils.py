from __future__ import annotations

import io
import logging
from subprocess import PIPE, Popen, run
from typing import Any

from PIL import Image


def _scaled_screenshot(screenshot_binary: bytes, width: int) -> Image:
    """
    Get scaled screenshot to fit driver window / element size

    :param screenshot_binary: original screenshot binary
    :param width: driver or element width
    :return: scaled image binary
    """
    img_binary = get_image(screenshot_binary)
    scale = img_binary.size[0] / width

    if scale != 1:
        new_image_size = (int(img_binary.size[0] / scale), int(img_binary.size[1] / scale))
        img_binary = img_binary.resize(new_image_size, Image.Resampling.LANCZOS)

    return img_binary


def get_image(screenshot_binary: bytes) -> Image.Image:
    """Open a PIL Image from raw screenshot bytes."""
    return Image.open(io.BytesIO(screenshot_binary))


def rescale_image(screenshot_binary: bytes, scale: int = 3, img_format: str = 'JPEG') -> bytes:
    """Rescale the given screenshot binary by the given scale factor and return new bytes."""
    img = get_image(screenshot_binary)
    img = img.resize((img.width // scale, img.height // scale), Image.Resampling.LANCZOS)

    return save_image(img, img_format)


def resize_image(image1: str, image2: str, img_format: str = 'JPEG') -> bytes:
    """Resize image1 to match the dimensions of image2 and return the result as bytes."""
    img1 = Image.open(image1)
    img2 = Image.open(image2)

    width, height = img2.size
    img1 = img1.resize((width, height), Image.Resampling.LANCZOS)

    return save_image(img1, img_format)


def save_image(img: Image.Image, img_format: str = 'JPEG') -> bytes:
    """Convert and save the given image to bytes in the specified format."""
    result_img_binary = io.BytesIO()
    img.convert('RGB').save(result_img_binary, format=img_format, optimize=True)
    return result_img_binary.getvalue()


def shell_running_command(cmd: str, **kwargs: Any) -> Popen:
    """Start a shell command as a background process and return the Popen object."""
    return Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True, **kwargs)  # noqa: S602


def shell_command(cmd: str, **kwargs: Any) -> Any:
    """Run a shell command synchronously and return the completed process object."""
    process = run(cmd, shell=True, check=False, **kwargs)  # noqa: S602

    if process.stdout:
        process.output = process.stdout.decode('utf8').replace('\n', '')
    if process.stderr:
        process.errors = process.stderr.decode('utf8').replace('\n', '')
    if isinstance(process.returncode, int):
        process.is_success = process.returncode == 0

    return process


def get_all_sub_elements(instance: Any, sub_elements: list | None = None) -> list:
    """Recursively collect all sub-elements from the given instance into a flat list."""
    if sub_elements is None:
        sub_elements = []

    if hasattr(instance, 'sub_elements') and instance.sub_elements:
        for sub_element in instance.sub_elements.values():
            sub_elements.append(sub_element)
            if hasattr(sub_element, 'sub_elements') and sub_element.sub_elements:
                get_all_sub_elements(sub_element, sub_elements)

    return sub_elements


def cut_log_data(data: str, length: int = 50) -> str:
    """
    Cut given data for reducing log length

    :param data: original data ~ 'very long string for typing. string endless continues'
    :param length: length to cut given data ~ 20
    :return: edited data ~ 'Type text: "very long string for >>> 36 characters"'
    """
    data = str(data)
    return f'{data[:length]} >>> {len(data[length:])} characters' if len(data) > length else data


def disable_logging(loggers: list) -> None:
    """
    Disable logging for given loggers

    :param loggers: list of loggers to be disabled
    :return: None
    """
    for logger in loggers:
        logging.getLogger(logger).disabled = True


def set_log_level(loggers: list, level: int) -> None:
    """
    Set log level for given loggers

    :param loggers: list of loggers to be disabled
    :param level: level to be set
    :return: None
    """
    for logger in loggers:
        logging.getLogger(logger).setLevel(level)

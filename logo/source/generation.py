#!/usr/bin/env python3
"""
A custom script to generate all the cdnjs logo variants from a set of source SVG designs
"""

import os
from enum import Enum
from io import BytesIO
from typing import Tuple, List, Dict, Union

from PIL import Image
from cairosvg import svg2png


class LogoVariant(Enum):
    """
    Tracks the different variants of the logo
    """

    dark = 1
    light = 2
    favicon = 3


class Color:
    """
    Class to store a 4 channel color
    """

    def __init__(self, red, green, blue, alpha):
        """
        :param red: The red channel value (0-255)
        :param green: The green channel value (0-255)
        :param blue: The blue channel value (0-255)
        :param alpha: The alpha channel value (0-255)
        """
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def tuple(self) -> Tuple[int, int, int, int]:
        """
        Outputs the four channels as a tuple
        :return: Tuple[int, int, int, int]: 4 channel color
        """
        return self.red, self.green, self.blue, self.alpha


class Colors:
    """
    Default colors used by the logos
    """

    dark: Color = Color(69, 70, 71, 255)  # 454647
    light: Color = Color(235, 235, 235, 255)  # EBEBEB
    transparent: Color = Color(0, 0, 0, 0)


class Logo:
    """
    Custom class to store a final logo render, alongside its size and variant information
    """

    def __init__(self, size: int, logo_variant: LogoVariant, bg_color: Color, image: Image):
        """
        :param size: The width/height of the image
        :param logo_variant: The type of the logo
        :param bg_color: The color of the logo background
        :param image: The final logo render as an Image
        """
        self.size = size
        self.__type = logo_variant
        self.__color = bg_color
        self.image = image
        self.__invert_dark = False
        self.directory = None

    @property
    def dark_file(self) -> bool:
        """
        Indicates if the file will be saved as a dark mode variant
        :return: bool: Dark file
        """
        if self.__type is LogoVariant.dark and not self.__invert_dark:
            return True
        if self.__type is LogoVariant.light and self.__invert_dark:
            return True
        if self.__type is LogoVariant.favicon and (self.__color is Colors.dark and not self.__invert_dark):
            return True
        if self.__type is LogoVariant.favicon and (self.__color is Colors.light and self.__invert_dark):
            return True
        return False

    @property
    def light_file(self) -> bool:
        """
        Indicates if the file will be saved as a light mode variant
        :return: bool: Light file
        """
        if self.__type is LogoVariant.light and not self.__invert_dark:
            return True
        if self.__type is LogoVariant.dark and self.__invert_dark:
            return True
        if self.__type is LogoVariant.favicon and (self.__color is Colors.light and not self.__invert_dark):
            return True
        if self.__type is LogoVariant.favicon and (self.__color is Colors.dark and self.__invert_dark):
            return True
        return False

    @property
    def filename(self) -> str:
        """
        Provides the full filename for the logo render as a PNG
        :return: str: Filename
        """
        return ("dark" if self.dark_file else ("light" if self.light_file else self.__type.name)) + \
               "-" + str(self.size) + ".png"

    def __validate_directory(self):
        """
        Ensures that the provided directory for the render is valid, creating it if not.
        """
        if self.directory:
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)

    def save(self, directory: str, *, invert_dark: bool = False) -> str:
        """
        Saves the logo render to the specified directory
        :param invert_dark: Allows the dark/light in the filename to be inverted (defaults to False)
        :param directory: The folder to save in
        :return: str: Filename where the logo was saved
        """
        self.directory = directory.rstrip("/")
        self.__validate_directory()
        self.__invert_dark = invert_dark
        filename = self.directory + "/" + self.filename
        self.image.save(filename, optimize=True)
        return filename


class ImageGenerator:
    """
    The main class for generating all the logo renderings from the source SVGs
    """

    def __init__(self):
        self.logo_width_multiplier: float = 0.8
        self.sizes: List[int] = [
            100,
            512,
            1024,
            2048
        ]
        self.base_logo_size: Dict[str, Tuple[int, int]] = {}

    @staticmethod
    def set_working_directory():
        """
        A method to ensure that the working directory for the script is the logo directory,
         one folder above the location of the generation script
        """
        script_directory = os.path.dirname(os.path.realpath(__file__))
        logo_directory = os.path.abspath(os.path.join(script_directory, os.pardir))
        os.chdir(logo_directory)

    @staticmethod
    def __create_base(size: int, color: Color) -> Image:
        """
        Creates the base image for any logo that will be rendered
        :param size: Width & height of base
        :param color: Background color (RGBA)
        :return: Image: Base image
        """
        return Image.new('RGBA', (size, size), color=color.tuple())

    def __get_logo_scale(self, filename: str, target_width: int) -> float:
        """
        Calculates the scale needed for the requested svg to reach the target width
        :param filename: Path to the SVG to be scaled
        :param target_width: The final width from which to calculate the scale
        :return: float: Scale
        """
        if filename not in self.base_logo_size:
            logo = svg2png(url=filename, scale=1)
            image = Image.open(BytesIO(logo))
            self.base_logo_size[filename] = (image.width, image.height)
            image.close()
        return target_width / self.base_logo_size[filename][0]

    def __get_logo_size(self, filename: str, target_width: int) -> Tuple[int, int]:
        """
        Calculates the height (and width) of the SVG file based on target width
        :param filename: SVG to calculate from
        :param target_width: The intended width from which to calculate the height
        :return: Tuple[int, int]: Width & Height
        """
        scale = self.__get_logo_scale(filename, target_width)
        return target_width, int(self.base_logo_size[filename][1] * scale)

    def __get_logo(self, width: int, logo_variant: LogoVariant, brackets: bool) -> Image:
        """
        Gets the logo at the desired width w/ or w/o brackets in the correct variant
        :param width: The target width of the final logo
        :param logo_variant: Which logo type should be used
        :param brackets: Should the logo have the brackets either side of the text
        :return: Image: Logo
        """
        logo_file = "source/" + logo_variant.name + ("-brackets" if brackets else "") + ".svg"
        size = self.__get_logo_size(logo_file, width)
        logo = svg2png(url=logo_file, output_width=size[0], output_height=size[1])
        image = Image.open(BytesIO(logo))
        return image

    @staticmethod
    def __overlay_logo(base: Image, logo: Image, mask: Image) -> Image:
        """
        Pastes the logo perfectly centered on the base image provided.
        :param base: The base image to overlay the logo on
        :param logo: The logo that will be pasted onto the base
        :param mask: The transparency mask that will be used for the paste (normally same as logo)
        :return: Image: Base & Logo combined
        """
        left = (base.width - logo.width) / 2
        top = (base.height - logo.height) / 2
        base.paste(logo, (int(left), int(top)), mask)
        return base

    def __generate(self, size: int, background: Color, *, logo_variant: LogoVariant = LogoVariant.dark,
                   brackets: bool = True, mono_overlay: Union[None, Color] = None,
                   custom_logo_width_multiplier: Union[None, float] = None) -> Logo:
        """
        Generate a logo render with the specified size, background and toggles for dark mode and brackets
        :param size: The final width/height of the rendered logo
        :param background: The background underneath the main logo
        :param logo_variant: The type of logo to be used for the render (defaults to dark)
        :param brackets: If the logo should include the brackets at either end of the text (defaults to True)
        :param mono_overlay: If provided, the logo will be of a single, solid color from this value (defaults to None)
        :param custom_logo_width_multiplier: If provided, the logo will be this % of full width (defaults to None)
        :return: Logo: The final logo render and relevant data
        """
        base = self.__create_base(size, background)
        logo = self.__get_logo(int(size * (custom_logo_width_multiplier or self.logo_width_multiplier)), logo_variant,
                               brackets)

        if mono_overlay is not None:
            mask = Image.new("RGBA", logo.size, mono_overlay.tuple())
            mask.putalpha(logo.getchannel("A"))
            logo = mask

        final = self.__overlay_logo(base, logo, logo)
        return Logo(size, logo_variant, background, final)

    def __generate_sizes(self, background: Color, *, logo_variant: LogoVariant = LogoVariant.dark,
                         brackets: bool = True, mono_overlay: Union[None, Color] = None,
                         custom_logo_width_multiplier: Union[None, float] = None) -> List[Logo]:
        """
        Generates a logo render for each predetermined size with specified the background, dark mode and brackets
        :param background: The background underneath the main logo
        :param logo_variant: The type of logo to be used for the render (defaults to dark)
        :param brackets: If the logos should include the brackets at either end of the text (defaults to True)
        :param mono_overlay: If provided, the logos will be of a single, solid color from this value (defaults to None)
        :param custom_logo_width_multiplier: If provided, the logos will be this % of full width (defaults to None)
        :return: List[Logo]: A list of all the final logo renders and their relevant data
        """
        results = []
        for size in self.sizes:
            results.append(self.__generate(size, background, logo_variant=logo_variant, brackets=brackets,
                                           mono_overlay=mono_overlay,
                                           custom_logo_width_multiplier=custom_logo_width_multiplier))
        return results

    @staticmethod
    def __save_all(logos: List[Logo], directory: str, *args, **kwargs):
        """
        Saves a list of logo renders to a specified directory, generating a preview README
        :param logos: The list of logo renders to be saved
        :param directory: The folder to save the logos to
        :param args: Additional args passed through to the save call
        :param kwargs: Additional keyword arguments passed to save
        """
        items = []
        for logo in logos:
            filename = logo.save(directory, *args, **kwargs)
            items.append([logo, filename])

        items = ["| {} | {} | {} | {} |".format(
            "<img src='https://github.com/cdnjs/brand/blob/master/logo/{}?raw=true' width='64' alt=''/>".format(f[1]),
            "{:,}px".format(f[0].size),
            "\N{WHITE HEAVY CHECK MARK}" if f[0].dark_file else "\N{CROSS MARK}",
            "[{}](https://github.com/cdnjs/brand/blob/master/logo/{})".format(f[0].filename, f[1])
        ) for f in items]
        items = "\n".join(items)
        with open("source/README.md") as file:
            template = file.read()
        template = template.format(directory=directory, table=items)
        with open(directory.rstrip("/") + "/README.md", "w+") as file:
            file.write(template)
        print("{:,} file{} saved to {}".format(len(logos), "" if len(logos) == 1 else "s", directory))

    def generate_standard(self):
        """
        Generates the "standard" folder of logos
        > Transparent BG with brackets
        """
        files = []
        files.extend(self.__generate_sizes(Colors.transparent, logo_variant=LogoVariant.dark))
        files.extend(self.__generate_sizes(Colors.transparent, logo_variant=LogoVariant.light))
        self.__save_all(files, "standard")

    def generate_social(self):
        """
        Generates the "social" folder of logos
        > Dark/light BG with brackets
        """
        files = []
        files.extend(self.__generate_sizes(Colors.light, logo_variant=LogoVariant.dark))
        files.extend(self.__generate_sizes(Colors.dark, logo_variant=LogoVariant.light))
        self.__save_all(files, "social", invert_dark=True)

    def generate_mono(self):
        """
        Generates the "mono" folder of logos
        > Transparent BG with brackets, solid color logo
        """
        files = []
        files.extend(self.__generate_sizes(Colors.transparent, logo_variant=LogoVariant.dark,
                                           mono_overlay=Colors.dark,
                                           custom_logo_width_multiplier=0.9))
        files.extend(self.__generate_sizes(Colors.transparent, logo_variant=LogoVariant.light,
                                           mono_overlay=Colors.light,
                                           custom_logo_width_multiplier=0.9))
        self.__save_all(files, "mono")

    def generate_simple(self):
        """
        Generates the "simple" folder of logos
        > Dark/light BG without brackets
        """
        files = []
        files.extend(self.__generate_sizes(Colors.light, logo_variant=LogoVariant.dark, brackets=False,
                                           custom_logo_width_multiplier=0.7))
        files.extend(self.__generate_sizes(Colors.dark, logo_variant=LogoVariant.light, brackets=False,
                                           custom_logo_width_multiplier=0.7))
        self.__save_all(files, "simple", invert_dark=True)

    def generate_favicon(self):
        """
        Generates the "favicon" folder of logos
        > Favicon on transparent background
        """
        files = []
        files.extend(self.__generate_sizes(Colors.transparent, logo_variant=LogoVariant.favicon, brackets=False,
                                           custom_logo_width_multiplier=0.9))
        self.__save_all(files, "favicon")

    def generate_icon(self):
        """
        Generates the "icon" folder of logos
        > Favicon on light/dark BG
        """
        files = []
        files.extend(self.__generate_sizes(Colors.light, logo_variant=LogoVariant.favicon, brackets=False,
                                           custom_logo_width_multiplier=0.9))
        files.extend(self.__generate_sizes(Colors.dark, logo_variant=LogoVariant.favicon, brackets=False,
                                           custom_logo_width_multiplier=0.9))
        self.__save_all(files, "icon")

    def generate_all(self):
        """
        Generates all the logo folders
        """
        self.generate_standard()
        self.generate_social()
        self.generate_mono()
        self.generate_simple()
        self.generate_favicon()
        self.generate_icon()


if __name__ == "__main__":
    generator = ImageGenerator()
    generator.set_working_directory()
    generator.generate_all()

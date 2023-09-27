# Copyright (C) 2023, Ali Haydar Güleç
# License: MIT License
from __future__ import annotations
import pathlib
import json
import random

import gradio as gr
from modules import scripts
from modules.ui_components import FormRow, FormColumn

TITLE = "Extended Style Selector"
DEFAULT_STYLE = "base"
DEFAULT_STYLE_FILE = "sdxl_styles.json"
MODE_SELECTED = "Selected Style For All Images"
MODE_RANDOM_ONE = "One Random Style For All Images"
MODE_RANDOM_EACH = "Random Style For Each Image"
MODE_GENERATE_IN_ORDER = "Use Styles In Order"


class JSONContentError(Exception):
    pass


class Style:
    def __init__(self, name: str, prompt: str, negative_prompt: str):
        self.name = name
        self.prompt = prompt
        self.negative_prompt = negative_prompt

    @staticmethod
    def parse(item: dict) -> Style:
        if not isinstance(item, dict):
            raise TypeError
        return Style(
            name=item.get("name", ""),
            prompt=item.get("prompt", ""),
            negative_prompt=item.get("negative_prompt", ""),
        )

    def create_positive(self, positive: str) -> str:
        return self.prompt.replace("{prompt}", positive)

    def create_negative(self, negative: str) -> str:
        negative_prompt = self.negative_prompt
        if negative_prompt:
            return f"{negative_prompt}, {negative}"
        return negative


class StyleFile:
    def __init__(self, json_data) -> None:
        self.styles: dict[str, Style] = load_json_content(json_data)

    def style_names(self) -> list[str]:
        return sorted(self.styles.keys())

    def create_positive(self, style_name: str, prompt: str) -> str:
        style = self.styles.get(style_name)
        if style:
            return style.create_positive(prompt)
        return prompt

    def create_negative(self, style_name: str, prompt: str) -> str:
        style = self.styles.get(style_name)
        if style:
            return style.create_negative(prompt)
        return prompt


def load_style_files() -> dict[str, StyleFile]:
    style_files: dict[str, StyleFile] = dict()
    for json_path in pathlib.Path(scripts.basedir()).glob("*.json"):
        try:
            json_data = json.loads(json_path.read_text(encoding="utf-8"))
        except (IOError, json.JSONDecodeError):
            print(f'{TITLE}: loading error, file "{json_path}" ignored')
            continue
        try:
            style_files[json_path.name] = StyleFile(json_data)
        except JSONContentError:
            print(f'{TITLE}: JSON parsing error, file "{json_path}" ignored')
    return style_files


def load_json_content(json_data: list[dict]) -> dict[str, Style]:
    styles: dict[str, Style] = {}
    if not isinstance(json_data, list):
        raise JSONContentError

    for item in json_data:
        try:
            style = Style.parse(item)
            styles[style.name] = style
        except TypeError:
            pass
    return styles


def get_default_style_name(style_names: list[str], default_style: str) -> str:
    if default_style not in style_names:
        try:
            default_style = style_names[0]
        except IndexError:
            default_style = ""
    return default_style


class ExtendedStyleSelector(scripts.Script):
    style_files: dict[str, StyleFile] = load_style_files()

    def title(self) -> str:
        return TITLE

    def show(self, is_img2img: bool):
        return scripts.AlwaysVisible

    def ui(self, is_img2img: bool):
        with gr.Group():
            with gr.Accordion("Extended Style Selector", open=False):
                style_filenames: list[str] = sorted(self.style_files.keys())
                default_filename = DEFAULT_STYLE_FILE
                if default_filename not in style_filenames:
                    if style_filenames:
                        default_filename = style_filenames[0]
                    else:
                        default_filename = ""

                style_names: list[str] = []
                style_file = self.style_files.get(default_filename)
                if style_file:
                    style_names = style_file.style_names()
                default_style_name = get_default_style_name(style_names, DEFAULT_STYLE)

                with FormRow():
                    is_enabled = gr.Checkbox(
                        value=False,
                        label="Active",
                    )
                with FormRow():
                    style_filename = gr.Dropdown(
                        choices=style_filenames,
                        value=default_filename,
                        type="value",
                        multiselect=False,
                        allow_custom_value=False,
                        interactive=True,
                        label="Style File",
                    )
                    style_name = gr.Dropdown(
                        style_names,
                        value=default_style_name,
                        type="value",
                        multiselect=False,
                        allow_custom_value=False,
                        interactive=True,
                        label="Style",
                    )
                style_filename.change(
                    self.on_change_style_file,
                    inputs=[style_filename],
                    outputs=[style_name],
                )
                with FormRow():
                    mode = gr.Radio(
                        choices=[
                            MODE_SELECTED,
                            MODE_RANDOM_ONE,
                            MODE_RANDOM_EACH,
                            MODE_GENERATE_IN_ORDER,
                        ],
                        type="value",
                        value=MODE_SELECTED,
                        interactive=True,
                        label="Mode",
                        info=f'Hint: disable "Dynamic Prompts" extension when using '
                        f'"{MODE_RANDOM_EACH}" or "{MODE_GENERATE_IN_ORDER}" option!',
                    )
        return [is_enabled, mode, style_filename, style_name]

    def on_change_style_file(self, filename: str):
        style_names: list[str] = []
        default_style: str = ""
        style_file = self.style_files.get(filename)
        if style_file:
            style_names = style_file.style_names()
            default_style = get_default_style_name(style_names, DEFAULT_STYLE)
        return gr.Dropdown.update(choices=style_names, value=default_style)

    def process(
        self, p, is_enabled: bool, mode: str, style_filename: str, style: str
    ) -> None:
        if not is_enabled:
            return
        style_file = self.style_files.get(style_filename)
        if not style_file:
            print(f'Style file "{style_filename}" not found.')
            return
        randomize = mode == MODE_RANDOM_ONE
        randomize_each = mode == MODE_RANDOM_EACH
        all_styles = mode == MODE_GENERATE_IN_ORDER

        style_names: list[str] = style_file.style_names()
        if randomize:
            style = random.choice(style_names)

        style_count: int = len(style_names)
        styles: list[str] = []
        # generate 'style_count' styles
        for i, prompt in enumerate(p.all_prompts):
            if all_styles:
                styles.append(style_names[i % style_count])
            elif randomize_each:
                styles.append(random.choice(style_names))
            else:
                styles.append(style)

        # assign generated style to positive prompts
        for i, prompt in enumerate(p.all_prompts):
            positive_prompt = style_file.create_positive(
                styles[i] if randomize_each or all_styles else style,
                prompt,
            )
            p.all_prompts[i] = positive_prompt

        # assign generated style to negative prompts
        for i, prompt in enumerate(p.all_negative_prompts):
            negative_prompt = style_file.create_negative(
                styles[i] if randomize_each or all_styles else style,
                prompt,
            )
            p.all_negative_prompts[i] = negative_prompt

        enable_hr = getattr(p, "enable_hr", False)  # exists only for txt2img
        if enable_hr:
            # copy prompts for hires.fix
            p.all_hr_prompts = p.all_prompts
            p.all_hr_negative_prompts = p.all_negative_prompts

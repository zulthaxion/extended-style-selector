# Copyright (C) 2023, Ali Haydar GÜLEÇ
# License: MIT License
from __future__ import annotations
from typing import Mapping
import pathlib
import json
import random

import gradio as gr
from modules import scripts
from modules.ui_components import FormRow, FormColumn

TITLE = "Extended Style Selector"
DEFAULT_STYLE = "base"


class JSONContentError(Exception):
    pass


class Style:
    def __init__(self, name: str, prompt: str, negative_prompt: str):
        self.name = name
        self.prompt = prompt
        self.negative_prompt = negative_prompt

    @classmethod
    def parse(cls, item: Mapping) -> Style:
        if not isinstance(item, Mapping):
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
    def __init__(self, json_data):
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


def load_json_content(json_data: list[Mapping]) -> dict[str, Style]:
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


def get_first_style_name(style_files) -> str:
    try:
        return list(style_files.keys())[0]
    except IndexError:
        return ""


class ExtendedStyleSelector(scripts.Script):
    style_files: dict[str, StyleFile] = load_style_files()
    current_style_file: str = get_first_style_name(style_files)

    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return TITLE

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def current_style_names(self) -> list[str]:
        style_file = self.style_files.get(self.current_style_file)
        if style_file:
            return style_file.style_names()
        return []

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("Extended Style Selector", open=False):
                style_file_names = list(self.style_files.keys())
                try:
                    first_file_name = style_file_names[0]
                except IndexError:
                    first_file_name = ""

                gr.HTML(
                    '<span>Info: disable "Dynamic Prompts" extension when using '
                    '"Generate All Styles In Order" or "Randomize For Each Iteration" option!</span>'
                )
                with FormRow():
                    with FormColumn(min_width=160):
                        is_enabled = gr.Checkbox(
                            value=False,
                            label="Enable Style Selector",
                            info="enable or disable style selector",
                        )
                    with FormColumn(elem_id="Randomize Style"):
                        randomize = gr.Checkbox(
                            value=False,
                            label="Randomize Style",
                            info="this overrides the selected style",
                        )
                    with FormColumn(elem_id="Randomize For Each Iteration"):
                        randomize_each = gr.Checkbox(
                            value=False,
                            label="Randomize For Each Iteration",
                            info="every prompt in batch will have a random style",
                        )

                style_files = gr.Dropdown(
                    choices=style_file_names,
                    value=first_file_name,
                    multiselect=False,
                    label="Select a Style File",
                )

                style_names: list[str] = self.current_style_names()
                with FormRow():
                    with FormColumn(min_width=160):
                        all_styles = gr.Checkbox(
                            value=False,
                            label="Generate All Styles In Order",
                            info="generate your prompt in all available styles, "
                            "set batch count accordingly",
                        )

                default_style_name = get_default_style_name(style_names, DEFAULT_STYLE)
                style = gr.Dropdown(
                    style_names,
                    value=default_style_name,
                    multiselect=False,
                    label="Select Style",
                )
                style_files.change(
                    self.on_change_style_file, inputs=[style_files], outputs=[style]
                )
        return [is_enabled, randomize, randomize_each, all_styles, style_files, style]

    def on_change_style_file(self, file_name):
        self.current_style_file = file_name
        style_names: list[str] = []
        default_style: str = ""
        style_file: StyleFile = self.style_files.get(file_name)
        if style_file:
            style_names = style_file.style_names()
            default_style = get_default_style_name(style_names, DEFAULT_STYLE)
        return gr.Dropdown.update(choices=style_names, value=default_style)

    def process(
        self, p, is_enabled, randomize, randomize_each, all_styles, style_files, style
    ):
        if not is_enabled:
            return
        style_file: StyleFile = self.style_files.get(self.current_style_file)
        if not style_file:
            print(f'Style file "{self.current_style_file}" not found.')
            return

        style_names: list[str] = style_file.style_names()
        if randomize:
            style = random.choice(style_names)
        batch_count: int = len(p.all_prompts)

        if batch_count == 1:
            p.all_prompts[0] = style_file.create_positive(style, p.all_prompts[0])
            p.all_negative_prompts[0] = style_file.create_negative(
                style, p.all_negative_prompts[0]
            )
        elif batch_count > 1:
            style_count: int = len(style_names)
            styles: list[str] = []
            for i, prompt in enumerate(p.all_prompts):
                if all_styles:
                    styles.append(style_names[i % style_count])
                elif randomize_each:
                    styles.append(random.choice(style_names))
                else:
                    styles.append(style)

            for i, prompt in enumerate(p.all_prompts):
                positive_prompt = style_file.create_positive(
                    styles[i] if randomize_each or all_styles else style,
                    prompt,
                )
                p.all_prompts[i] = positive_prompt
            for i, prompt in enumerate(p.all_negative_prompts):
                negative_prompt = style_file.create_negative(
                    styles[i] if randomize_each or all_styles else style,
                    prompt,
                )
                p.all_negative_prompts[i] = negative_prompt
        if p.enable_hr:
            p.all_hr_prompts = p.all_prompts
            p.all_hr_negative_prompts = p.all_negative_prompts

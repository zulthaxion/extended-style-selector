from __future__ import annotations
import pathlib

import gradio as gr
from modules import scripts, shared, script_callbacks
from modules.ui_components import FormRow, FormColumn
import json
import random

try:
    import sd_dynamic_prompts

    SD_DYNAMIC_PROMPTS_INSTALLED = True
except ImportError:
    SD_DYNAMIC_PROMPTS_INSTALLED = False

DEFAULT_STYLE_FILE = "sdxl_styles.json"
DEFAULT_STYLE = "base"


class StyleFile:
    def __init__(self, path: pathlib.Path, names: list[str]):
        self.file_path = path
        self.style_names = names


def load_style_files() -> dict[str, StyleFile]:
    style_files = dict()
    for json_path in pathlib.Path(scripts.basedir()).glob("*.json"):
        json_data = get_json_content(json_path)
        style_files[json_path.name] = StyleFile(json_path, read_sdxl_styles(json_data))
    return style_files


def get_json_content(file_path):
    try:
        with open(file_path, "rt", encoding="utf-8") as file:
            json_data = json.load(file)
            return json_data
    except Exception as e:
        print(f"A Problem occurred: {str(e)}")


def read_sdxl_styles(json_data):
    # Check that data is a list
    if not isinstance(json_data, list):
        print("Error: input data must be a list")
        return None

    names = []

    # Iterate over each item in the data list
    for item in json_data:
        # Check that the item is a dictionary
        if isinstance(item, dict):
            # Check that 'name' is a key in the dictionary
            if "name" in item:
                # Append the value of 'name' to the names list
                names.append(item["name"])
    names.sort()
    return names


def create_positive(style, positive, json_path: pathlib.Path):
    json_data = get_json_content(json_path)
    try:
        # Check if json_data is a list
        if not isinstance(json_data, list):
            raise ValueError("Invalid JSON data. Expected a list of templates.")

        for template in json_data:
            # Check if template contains 'name' and 'prompt' fields
            if "name" not in template or "prompt" not in template:
                raise ValueError("Invalid template. Missing 'name' or 'prompt' field.")

            # Replace {prompt} in the matching template
            if template["name"] == style:
                positive = template["prompt"].replace("{prompt}", positive)

                return positive

        # If function hasn't returned yet, no matching template was found
        raise ValueError(f"No template found with name '{style}'.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def create_negative(style, negative, json_path: pathlib.Path):
    json_data = get_json_content(json_path)
    try:
        # Check if json_data is a list
        if not isinstance(json_data, list):
            raise ValueError("Invalid JSON data. Expected a list of templates.")

        for template in json_data:
            # Check if template contains 'name' and 'prompt' fields
            if "name" not in template or "prompt" not in template:
                raise ValueError("Invalid template. Missing 'name' or 'prompt' field.")

            # Replace {prompt} in the matching template
            if template["name"] == style:
                json_negative_prompt = template.get("negative_prompt", "")
                if negative:
                    negative = (
                        f"{json_negative_prompt}, {negative}"
                        if json_negative_prompt
                        else negative
                    )
                else:
                    negative = json_negative_prompt

                return negative

        # If function hasn't returned yet, no matching template was found
        raise ValueError(f"No template found with name '{style}'.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def get_default_style_name(style_names: list[str], default_style: str) -> str:
    if default_style not in style_names:
        try:
            default_style = style_names[0]
        except IndexError:
            default_style = ""
    return default_style


class StyleSelectorXL(scripts.Script):
    style_files = load_style_files()
    current_style_file = DEFAULT_STYLE_FILE

    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return "Extended Style Selector"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def current_style_names(self) -> list[str]:
        return self.style_files[self.current_style_file].style_names

    def ui(self, is_img2img):
        enabled = getattr(shared.opts, "enable_styleselector_by_default", True)
        style_names = self.current_style_names()
        with gr.Group():
            with gr.Accordion("Extended Style Selector", open=False):
                style_file_names = list(self.style_files.keys())
                try:
                    first_file_name = style_file_names[0]
                except IndexError:
                    first_file_name = ""

                if SD_DYNAMIC_PROMPTS_INSTALLED:
                    gr.HTML(
                        '<span>Info: disable "Dynamic Prompts extension" when using '
                        '"Generate All Styles In Order" or "Randomize For Each Iteration" option!</span>'
                    )
                with FormRow():
                    with FormColumn(min_width=160):
                        is_enabled = gr.Checkbox(
                            value=enabled,
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

                with FormRow():
                    with FormColumn(min_width=160):
                        all_styles = gr.Checkbox(
                            value=False,
                            label="Generate All Styles In Order",
                            info=f"to generate your prompt in all available styles, "
                            f"set batch count to {len(style_names)} (style count)",
                        )

                default_style = get_default_style_name(style_names, DEFAULT_STYLE)
                style_ui_type = shared.opts.data.get("styles_ui", "radio-buttons")
                if style_ui_type == "select-list":
                    style = gr.Dropdown(
                        style_names,
                        value=default_style,
                        multiselect=False,
                        label="Select Style",
                    )
                else:
                    style = gr.Radio(
                        label="Style", choices=style_names, value=default_style
                    )
                style_files.change(
                    self.on_change_style_file, inputs=[style_files], outputs=[style]
                )
        # Ignore the error if the attribute is not present
        return [is_enabled, randomize, randomize_each, all_styles, style_files, style]

    def on_change_style_file(self, file_name):
        self.current_style_file = file_name
        style_names = self.style_files[file_name].style_names
        default_style = get_default_style_name(style_names, DEFAULT_STYLE)
        return gr.Dropdown.update(choices=style_names, value=default_style)

    def process(
        self, p, is_enabled, randomize, randomize_each, all_styles, style_files, style
    ):
        if not is_enabled:
            return
        style_names = self.current_style_names()
        json_path = self.style_files[self.current_style_file].file_path

        if randomize:
            style = random.choice(style_names)
        batch_count = len(p.all_prompts)

        if batch_count == 1:
            p.all_prompts[0] = create_positive(style, p.all_prompts[0], json_path)
            p.all_negative_prompts[0] = create_negative(
                style, p.all_negative_prompts[0], json_path
            )
        elif batch_count > 1:
            style_count = len(style_names)
            styles = []
            for i, prompt in enumerate(p.all_prompts):
                if all_styles:
                    styles.append(style_names[i % style_count])
                elif randomize_each:
                    styles.append(random.choice(style_names))
                else:
                    styles.append(style)

            # for each image in batch
            for i, prompt in enumerate(p.all_prompts):
                positive_prompt = create_positive(
                    styles[i] if randomize_each or all_styles else style,
                    prompt,
                    json_path,
                )
                p.all_prompts[i] = positive_prompt
            for i, prompt in enumerate(p.all_negative_prompts):
                negative_prompt = create_negative(
                    styles[i] if randomize_each or all_styles else style,
                    prompt,
                    json_path,
                )
                p.all_negative_prompts[i] = negative_prompt

        p.extra_generation_params["Style Selector Enabled"] = True
        p.extra_generation_params["Style Selector Randomize"] = randomize
        p.extra_generation_params["Style Selector Style"] = style


def on_ui_settings():
    section = ("styleselector", "Style Selector")
    shared.opts.add_option(
        "styles_ui",
        shared.OptionInfo(
            "radio-buttons",
            "How should Style Names Rendered on UI",
            gr.Radio,
            {"choices": ["radio-buttons", "select-list"]},
            section=section,
        ),
    )

    shared.opts.add_option(
        "enable_styleselector_by_default",
        shared.OptionInfo(
            True, "enable Style Selector by default", gr.Checkbox, section=section
        ),
    )


script_callbacks.on_ui_settings(on_ui_settings)

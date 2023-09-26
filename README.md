## Extended Style Selector

This repository contains a Automatic1111 Extension allows users to select and apply 
different styles to their inputs using any Stable Diffusion model.

This extension is a fork of [Style Selector for SDXL 1.0](https://github.com/ahgsql/StyleSelectorXL.git) 
by Ali Haydar GÜLEÇ. I renamed the extension to Extended Style Selector because it works 
with SDXL 1.0 and any other model as well. 

### Styles

Released positive and negative templates are used to generate stylized prompts. Just 
install extension, then styles will appear in the panel as a dropdown selector.

I added support for multiple style files.

### Installation

Enter this repo's URL in Automatic1111's extension tab "Install from Url":

https://github.com/mozman/ExtenedStyleSelector

### Usage

Enable or disable the extension (default is disabled). 
Write your subject into the prompt field, select a style then hit generate! The selected 
style will be applied to the current prompt.

### Thanks

Thanks to Ali Haydar GÜLEÇ for creating [Style Selector for SDXL 1.0](https://github.com/ahgsql/StyleSelectorXL.git).

Huge thanks for https://github.com/twri/sdxl_prompt_styler as I got style json file's 
original structure from his repo.

Thanks to [Diva](https://civitai.com/user/Diva/models) for the Art Styles Expansion file: 
https://civitai.com/models/132426/art-styles-expansion-for-styleselectorxl?modelVersionId=145656

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

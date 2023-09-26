## Extended Style Selector

This repository contains an Automatic1111 extension that applies styles to 
the input prompts. The Styles are stored in one or multiple JSON files in the 
extension directory.

This extension is a fork of [Style Selector for SDXL 1.0](https://github.com/ahgsql/StyleSelectorXL.git) 
by Ali Haydar Güleç. The extension was renamed to "Extended Style Selector" because the 
extension works with SDXL as well as with any other Stable Diffusion model (1.5 & 2.1). 

### Styles

The included style files contain positive and negative prompt templates to generate 
stylized prompts. The extension can be used in "txt2img" and "img2img" tabs.

### Installation

Enter this repo's URL in Automatic1111's extension tab "Install from Url":

https://github.com/mozman/ExtendedStyleSelector

### Usage

Active the extension (default is disabled). 
Write your prompts, select a style file and a style then hit generate! 
The selected style will be applied to your prompts.

### Modes

The count of generated images is determined by the batch count.

- **selected style for all images:** All generated images have the same style.
- **one random style for all images:** A random style will be chosen to generate all images, 
  the selected style is ignored.
- **random style for each image:** All generated images have a random style.
- **use style in order:** The styles of the selected style file are applied in ascending 
  alphabetically order. Set batch count to the count of styles in the style file to render 
  all styles. The rendering process cycles through all styles if there are fewer styles than 
  images to render. 

### Thanks

- to Ali Haydar Güleç for creating the [Style Selector for SDXL 1.0](https://github.com/ahgsql/StyleSelectorXL.git) extension
- to https://github.com/twri/sdxl_prompt_styler for the original style json files
- to [Diva](https://civitai.com/user/Diva/models) for the Art Styles Expansion [file](https://civitai.com/models/132426/art-styles-expansion-for-styleselectorxl?modelVersionId=145656)

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

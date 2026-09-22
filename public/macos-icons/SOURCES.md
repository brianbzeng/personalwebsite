# macOS Tahoe desktop assets

Integrated September 5, 2026. Native artwork is kept intact, including the icon's own rounded background and intrinsic alpha outside its silhouette. The desktop applies grayscale through CSS; these are not AI-generated cutouts. All served assets are local files.

## Apple-hosted app and system icons

- Notes (400×400): [Apple Notes guide](https://support.apple.com/en-au/guide/notes/welcome/mac), [PNG](https://help.apple.com/assets/68CC860E47105BA9B400F778/68CC861147105BA9B400F77E/en_AU/addbfeb30b8f7cead2b677a40b9a630e.png). Original artwork and alpha preserved; grayscale is applied by the desktop.
- Terminal (400×400): [Apple Terminal guide](https://support.apple.com/guide/terminal/welcome/mac), [PNG](https://help.apple.com/assets/67DB80CC8ED20D93270BDBE5/67DB80CD888B30021203ACDC/en_US/71142b814e58f29c2e808244a3ef5877.png).
- Contacts, used for About Brian (400×400): [Apple Contacts guide](https://support.apple.com/guide/contacts/welcome/mac), [PNG](https://help.apple.com/assets/6940565209A94A9B200A40A9/69405653B52840D87D012299/en_US/7f52b6a8a42927374571f4ead913072a.png).
- Mail, used for Contact (400×400): [Apple Mail guide](https://support.apple.com/guide/mail/welcome/mac), [PNG](https://help.apple.com/assets/6940590395B73B67500DF914/69405904627DAC39E4013406/en_US/610a7e660092193773855879a591dc48.png).
- Help (60×60): Apple's circular Help control, not a fabricated Help app tile. [Apple guide](https://support.apple.com/en-gb/guide/mac-help/mh15217/mac), [PNG](https://help.apple.com/assets/69DD569682238CF8EC0621E2/69DD569982238CF8EC0621E9/en_GB/8bd8fd5a025ce3eab5e21828cdc1a861.png).
- Apple menu logo (48×60, black original, inverted for white display): [Apple menu guide](https://support.apple.com/guide/mac-help/whats-in-the-apple-menu-mchlp1130/mac), [PNG](https://help.apple.com/assets/69DD569682238CF8EC0621E2/69DD569982238CF8EC0621E9/en_US/2f77cc85238452e25cb517130188bf99.png).

## Empty Trash

The Terminal titlebar folder proxy icon (folder.png, 256×256) is the native Tahoe folder from the same Sketch-resource mirror: [direct file](https://raw.githubusercontent.com/MiaowCham/macOS_Tahoe_Themes_for_MDF/main/macOS%20Tahoe%2026/icons/Light/folder.png). Original artwork preserved, displayed at 16px in grayscale; provenance remains the mirror maintainer's attribution to Apple's UI kit.

- Dark native empty-bin PNG, 256×256: [direct file](https://raw.githubusercontent.com/MiaowCham/macOS_Tahoe_Themes_for_MDF/main/macOS%20Tahoe%2026/icons/Dark/Trash%20Empty.png).
- The [mirror's README](https://github.com/MiaowCham/macOS_Tahoe_Themes_for_MDF) attributes this directory to Apple's macOS Tahoe Sketch UI kit. This is the maintainer's provenance statement, not independent byte verification against the Sketch file. Apple's guide supplies only a smaller full-bin icon; it was not used because this desktop's Trash is empty.

## Wallpaper

- Original: [Tahoe Dark 6K PNG](https://media.512pixels.net/downloads/macos-wallpapers-6k/26-Tahoe-Dark-6K.png).
- [512 Pixels extraction record](https://512pixels.net/2025/06/macos-tahoe-beta-wallpaper/) identifies it as extracted macOS Tahoe system wallpaper.
- Served as /macos-tahoe-dark.jpg: resized from 6016×6016 to 2560×2560, JPEG quality 90, complete square composition preserved, 301152 bytes. CSS cover fills the viewport; CSS grayscale supplies the monochrome appearance.

Apple retains ownership of its artwork. No permissive redistribution license was identified. Review asset permissions before public distribution; this iteration remains local.

## Behavior and styling references

- [Tahoe design announcement](https://www.apple.com/newsroom/2025/06/macos-tahoe-26-makes-the-mac-more-capable-productive-and-intelligent-than-ever/): Liquid Glass, clear menu bar, rounder windows, native icon appearance options.
- [Icon appearances](https://developer.apple.com/design/human-interface-guidelines/app-icons): default, dark, clear, and tinted are options; clear is not mandatory.
- [Dock settings](https://support.apple.com/guide/mac-help/change-desktop-dock-settings-mchlp1119/26/mac/26): magnification, auto-hide, bounce, running indicators.
- [Terminal shell](https://support.apple.com/guide/terminal/change-the-default-shell-trml113/mac): zsh default. The brian@Mac prompt is customized for this portfolio, not a claim about the visitor's computer.
- [Terminal text settings](https://support.apple.com/guide/terminal/change-profiles-text-settings-trmltxt/mac): configurable underline cursor.

This is a browser adaptation, not an OS session. Commands still dispatch existing in-page content; no shell process is started. Dock timing/cosine magnification, grayscale window controls, and scale minimization are implementation choices, not pixel-exact Apple specifications.

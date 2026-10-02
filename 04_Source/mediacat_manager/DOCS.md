# MediaCat Manager

The ASTV-277 release is an authenticated Ingress shell and governed safety
foundation. It does not yet edit catalogue files.

After installation, open **MediaCat Manager** from the Home Assistant sidebar.
The shell reports the configured catalogue, asset and history boundaries.

Required local paths:

- catalogues: `/config/mediacat/catalogues/` (container path
  `/homeassistant/mediacat/catalogues/`);
- assets: `/config/www/ha-assets/` (read-only application policy; container
  path `/homeassistant/www/ha-assets/`);
- Manager history: App-private `/data/history/`.

MediaCat must provide version 1 of its governed administration interface before
the later ASTV-286 editor workflow is enabled.

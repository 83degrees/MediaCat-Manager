# MediaCat Manager

MediaCat Manager is an authenticated Ingress catalogue editor built on the
ASTV-277 safety foundation and completed by ASTV-286.

After installation, open **MediaCat Manager** from the Home Assistant sidebar.
The UI discovers catalogues by their in-file `catalogue_id`, provides typed item
and category controls, validates complete candidates through MediaCat, performs
atomic replacement, and reports structured reload results.

Required local paths:

- catalogues: `/config/mediacat/catalogues/` (container path
  `/homeassistant/mediacat/catalogues/`);
- assets: `/config/www/ha-assets/` (read-only application policy; container
  path `/homeassistant/www/ha-assets/`);
- Manager history: App-private `/data/history/`.

MediaCat must provide version 1 of its governed administration interface.
History snapshots are retained under App-private `/data/history/`, and the
visual artwork picker can read but never modify the `ha-assets` mirror.

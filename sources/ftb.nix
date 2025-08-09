{pkgs, ...}: {
  "server-installer" = pkgs.fetchurl {
    url = "https://api.github.com/repos/FTBTeam/FTB-Server-Installer/releases/assets/271415605";
    sha256 = "1apg47bym7w06cicvny0czq3nmaav53l9pv30dvj77p5fafwgf3x";
  };
}

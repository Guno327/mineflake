{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  languages.python = {
    enable = true;
    venv = {
      enable = true;
      requirements = ./requirments.txt;
    };
  };

  packages = with pkgs; [
    sqlite
  ];
}

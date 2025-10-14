{
  lib,
  pkgs,
  ...
}:
with lib; {
  pack = mkOption {
    type = types.str;
    description = "id for FTB, slug for cf";
  };
}

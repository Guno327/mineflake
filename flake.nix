{
  description = "Mineflake - A dedicated minecraft server nixos module";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    nixosModules = {
      vanilla = import ./modules/vanilla.nix;
    };
  };
}

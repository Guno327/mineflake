{pkgs ? import <nixpkgs> {}}: let
  inherit (pkgs) lib stdenv;
in
  pkgs.mkShell {
    NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
      stdenv.cc.cc
    ];
    NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";

    buildInputs = [
      (pkgs.python3.withPackages
        (p: [
          p.jsondiff
          p.requests
          p.tqdm
        ]))
      pkgs.sqlite
    ];
  }

{
  config,
  lib,
  pkgs,
  ...
}: let
  cf_sources = import ../sources/curseforge.nix;
  cfg = config.mineflake.curseforge;
  pack = cf_sources."${cfg.pack}:${cfg.version}";

  server = pkgs.stdenv.mkDerivation {
    pname = "mineflake-server";
    version = "${cfg.pack}:${cfg.version}";

    src = pkgs.fetchurl (pack.zip);
    buildInputs = [cfg.java];
    phases = ["installPhase"];

    serverProperties = pkgs.writeText "server.properties" (lib.generators.toKeyValue {} cfg.serverProperties);

    eula = pkgs.writeText "eula.txt" ''
      #By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
      eula=${cfg.eula}
    '';

    installPhase = ''
      mkdir -p $out
      cp -r $src/* $out

      chmod +x $out/${pack.script}
    '';
  };

  stdOptions = import ../options/std.nix {inherit lib pkgs;};
  moddedOptions = import ../options/modded.nix {inherit lib pkgs;};
  serverPropertyOptions = import ../options/server-properties.nix {inherit lib;};
in
  with lib; {
    options.mineflake.curseforge = mergeAttrsList [
      stdOptions
      serverPropertyOptions
      moddedOptions
    ];

    config = mkIf cfg.enable {
      users = {
        users.minecraft = {
          name = "minecraft";
          isSystemUser = true;
          home = "${cfg.dir}";
          group = "minecraft";
        };
        groups.minecraft = {};
      };

      environment.systemPackages = [server cfg.java pkgs.udev];
      systemd.services."mineflake-server" = {
        enable = true;
        wantedBy = ["multi-user.target"];
        serviceConfig = {
          Type = "exec";
          User = "minecraft";
          Group = "minecraft";

          Restart = "on-failure";
          StandardOutput = "journal";
          StandardError = "journal";
          RemainAfterExit = "no";
        };

        path = [pkgs.udev];

        preStart = ''
          mkdir -p ${cfg.dir}
          mkdir -p ${cfg.dir}/${cfg.name}
          cp -f ${server}/* ${cfg.dir}/${cfg.name}/
        '';

        script = ''
          cd ${cfg.dir}/${cfg.name}
          exec ./${pack.script}
        '';
      };
    };
  }

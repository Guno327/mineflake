{
  config,
  lib,
  pkgs,
  ...
}: let
  vanilla_sources = import ../sources/vanilla.nix;
  cfg = config.mineflake.vanilla;

  server = pkgs.stdenv.mkDerivation {
    pname = "mineflake-server";
    version = "${cfg.version}";

    jar = pkgs.fetchurl (vanilla_sources.${cfg.version});
    buildInputs = [cfg.java];
    phases = ["installPhase"];

    serverProperties = pkgs.writeText "server.properties" (lib.generators.toKeyValue {} cfg.serverProperties);

    eula = pkgs.writeText "eula.txt" ''
      #By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
      eula=${cfg.eula}
    '';

    installPhase = ''
      mkdir $out
      cp $jar $out/server.jar
      cp $serverProperties $out/server.properties
      cp $eula $out/eula.txt
    '';
  };

  stdOptions = import ../options/std.nix {inherit lib pkgs;};
  serverPropertyOptions = import ../options/server-properties.nix {inherit lib;};
in
  with lib; {
    options.mineflake.vanilla = mergeAttrsList [
      stdOptions
      serverPropertyOptions
    ];

    config = mkIf cfg.enable {
      environment.systemPackages = [server cfg.java pkgs.udev];

      users = {
        users.minecraft = {
          name = "mineflake";
          isSystemUser = true;
          group = "mineflake";
          createHome = false;
        };
        groups.mineflake = {};
      };

      systemd.tmpfiles.rules = [
        "d ${cfg.dir} 0755 mineflake mineflake -"
        "d ${cfg.dir}/${cfg.name} 0755 mineflake mineflake"
      ];

      systemd.services."mineflake-server" = {
        enable = true;
        wantedBy = ["multi-user.target"];
        serviceConfig = {
          Type = "exec";
          User = "mineflake";
          Group = "mineflake";

          WorkingDirectory = "${cfg.dir}/${cfg.name}";
          ExecStart = "${cfg.java}/bin/java ${cfg.flags} -jar ${server}/server.jar";

          Restart = "on-failure";
          StandardOutput = "journal";
          StandardError = "journal";
          RemainAfterExit = "no";
        };
        path = [pkgs.udev];

        preStart = ''
          cp -rf ${server}/* ${cfg.dir}/${cfg.name}/
        '';
      };
    };
  }

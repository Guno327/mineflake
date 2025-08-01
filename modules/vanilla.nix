{
  config,
  pkgs,
  lib,
  ...
}: let
  vanilla_sources = import ../sources/vanilla.nix {inherit pkgs;};
  cfg = config.mineflake.vanilla;
  server-jar = pkgs.stdenv.mkDerivation {
    pname = "server-jar";
    version = "${cfg.version}";

    jar = vanilla_sources.${cfg.version};
    buildInputs = [cfg.java];
    phases = ["installPhase"];

    installPhase = ''
      mkdir -p $out/bin
      cp $jar $out/bin/server.jar
    '';
  };
in
  with lib; {
    options.mineflake.vanilla = {
      enable = mkEnableOption "Enable vanilla server";

      version = mkOption {
        type = types.str;
        default = "latest";
        description = "Server version";
      };

      dir = mkOption {
        type = types.path;
        default = "/var/lib/minecraft";
        description = "Directory to store server files";
      };

      name = mkOption {
        type = types.str;
        default = "server";
        description = "Name of server, determines sub-dir name";
      };

      flags = mkOption {
        type = types.str;
        default = "-Xmx1024M -Xms1024M";
        description = "Server launch flags";
      };

      java = mkOption {
        type = types.package;
        default = pkgs.jdk17;
        description = "Java package to use to run server";
      };
    };

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

      systemd.tmpfiles.rules = [
        "d ${cfg.dir} 774 minecraft minecraft -"
        "d ${cfg.dir}/${cfg.name} 774 minecraft minecraft -"
      ];

      environment.systemPackages = [server-jar cfg.java];
      systemd.services."mineflake-server" = {
        enable = true;
        wantedBy = ["multi-user.target"];
        serviceConfig = {
          Type = "exec";
          User = "minecraft";
          Group = "minecraft";
          Restart = "always";
        };
        script = ''
          cd ${cfg.dir}
          java ${cfg.flags} -jar ${server-jar}/bin/server.jar
        '';
      };
    };
  }

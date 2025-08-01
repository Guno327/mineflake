{
  config,
  pkgs,
  lib,
  vanilla_sources,
  ...
}: let
  cfg = config.mineflake.vanilla;
  vanilla-server = pkgs.stdenv.mkDerivation {
    pname = "minecraft-vanilla-server";
    version = "${cfg.version}";

    jar = vanilla_sources.${cfg.version};
    buildInputs = [cfg.java pkgs.makeWrapper];
    phases = ["installPhase"];

    installPhase = ''
      mkdir -p $out/bin
      cp $jar $out/bin/server.jar

      cat > $out/bin/minecraft-vanilla-server << 'EOF'
        #!/bin/sh
        cd ${cfg.dir}
        java ${cfg.flags} -jar $out/bin/server.jar
      EOF

      chmod +x $out/bin/minecraft-vanilla-server
      wrapProgram $out/bin/minecraft-vanilla-server \
        --set PATH : ${lib.mkBinPath [cfg.java]}
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
        type = type.str;
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
          home = "${dir}";
          group = "minecraft";
        };
        groups.minecraft = {};
      };

      systemd.tmpfiles.rules = [
        "d ${dir} 774 minecraft minecraft -"
        "d ${dir}/${name} 774 minecraft minecraft -"
      ];

      environment.systemPackages = [vanilla-server];
      systemd.services."minecraft-server-${name}" = {
        wantedBy = ["multi-user.target"];
        serviceConfig = {
          Type = "exec";
          User = "minecraft";
          Group = "minecraft";
          ExecStart = "${vanilla-server}/bin/minecraft-vanilla-server";
          Restart = "always";
        };
      };
    };
  }

{
  config,
  pkgs,
  lib,
  ...
}: let
  vanilla_sources = import ../sources/vanilla.nix {inherit pkgs;};
  cfg = config.mineflake.vanilla;

  server = pkgs.stdenv.mkDerivation {
    pname = "server-jar";
    version = "${cfg.version}";

    jar = vanilla_sources.${cfg.version};
    buildInputs = [cfg.java];
    phases = ["installPhase"];

    installPhase = ''
      cp $jar $out/server.jar
      echo ${lib.generators.toKeyValue {} cfg.serverProperties} > $out/server.properties

      echo <<EOF > $out/eula.txt
      #By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
      eula=${cfg.eula}
      EOF

      echo <<EOF > $out/start.sh
      #!/bin/sh
      exec ${cfg.java}/bin/java ${cfg.flags} -jar server.jar
      EOF

      chmod +x $out/start.sh
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
        default = pkgs.jdk21;
        description = "Java package to use to run server";
      };

      eula = mkOption {
        type = types.bool;
        default = false;
        description = "Whether to accept the EULA";
      };

      serverProperties = mkOption {
        description = "Overrides for server.properties file";
        type = with types;
          submodule {
            options = {
              accepts-transfers = mkOption {
                type = bool;
                default = false;
              };
              allow-flight = mkOption {
                type = bool;
                default = false;
              };
              allow-nether = mkOption {
                type = bool;
                default = true;
              };
              broadcast-console-to-ops = mkOption {
                type = bool;
                default = true;
              };
              broadcast-rcon-to-ops = mkOption {
                type = bool;
                default = true;
              };
              bug-report-link = mkOption {
                type = str;
                default = "";
              };
              difficulty = mkOption {
                type = enum ["easy" "normal" "hard"];
                default = "easy";
              };
              enable-command-block = mkOption {
                type = bool;
                default = false;
              };
              enable-jmx-monitoring = mkOption {
                type = bool;
                default = false;
              };
              enable-query = mkOption {
                type = bool;
                default = false;
              };
              enable-rcon = mkOption {
                type = bool;
                default = false;
              };
              enable-status = mkOption {
                type = bool;
                default = true;
              };
              enforce-secure-profile = mkOption {
                type = bool;
                default = true;
              };
              enforce-whitelist = mkOption {
                type = bool;
                default = false;
              };
              entity-broadcast-range-percentage = mkOption {
                type = int.mkCheck (x: x >= 10 && x <= 1000);
                default = 100;
              };
              force-gamemode = mkOption {
                type = bool;
                default = false;
              };
              function-permission-level = mkOption {
                type = int.mkCheck (x: x >= 1 && x <= 4);
                default = 2;
              };
              gamemode = mkOption {
                type = enum ["survival" "creative" "adventure" "spectator"];
                default = "survival";
              };
              generate-structures = mkOption {
                type = bool;
                default = true;
              };
              generator-settings = mkOption {
                type = str;
                default = "{}";
              };
              hardcore = mkOption {
                type = bool;
                default = false;
              };
              hide-online-players = mkOption {
                type = bool;
                default = false;
              };
              initial-enabled-packs = mkOption {
                type = str;
                default = "vanilla";
              };
              level-name = mkOption {
                type = str;
                default = "world";
              };
              level-seed = mkOption {
                type = str;
                default = "";
              };
              level-type = mkOption {
                type = str;
                default = "minecraft:normal";
              };
              max-chained-neighbor-updates = mkOption {
                type = int;
                default = 1000000;
              };
              max-players = mkOption {
                type = int;
                default = 20;
              };
              max-tick-time = mkOption {
                type = int;
                deault = 60000;
              };
              max-world-size = mkOption {
                type = int.mkCheck (x: x >= 1 && x <= 29999984);
                default = 29999984;
              };
              motd = mkOption {
                type = str;
                default = "A Mineflake Server";
              };
              network-compression-threshold = mkOption {
                type = int;
                default = 256;
              };
              online-mode = mkOption {
                type = bool;
                default = true;
              };
              op-permission-level = mkOption {
                type = int.mkCheck (x: x >= 1 && x <= 4);
                default = 4;
              };
              player-idle-timeout = mkOption {
                type = int;
                default = 0;
              };
              prevent-proxy-connections = mkOption {
                type = bool;
                default = false;
              };
              previews-chat = mkOption {
                type = bool;
                default = false;
              };
              pvp = mkOption {
                type = bool;
                default = true;
              };
              query.port = mkOption {
                type = int;
                default = 25565;
              };
              rate-limit = mkOption {
                type = int;
                default = 0;
              };
              rcon.password = mkOption {
                type = str;
                default = "";
              };
              rcon.port = mkOption {
                type = int;
                default = 25575;
              };
              resource-pack = mkOption {
                type = str;
                default = "";
              };
              resource-pack-prompt = mkOption {
                type = str;
                default = "";
              };
              resource-pack-sha1 = mkOption {
                type = str;
                default = "";
              };
              require-resource-pack = mkOption {
                type = bool;
                default = false;
              };
              server-ip = mkOption {
                type = str;
                default = "";
              };
              server-port = mkOption {
                type = int;
                default = 25565;
              };
              simulation-distance = mkOption {
                type = int.mkCheck (x: x >= 3 && x <= 32);
                default = 10;
              };
              snooper-enabled = mkOption {
                type = bool;
                default = true;
              };
              spawn-animals = mkOption {
                type = bool;
                default = true;
              };
              spawn-monters = mkOption {
                type = bool;
                default = true;
              };
              spawn-npcs = mkOption {
                type = bool;
                default = true;
              };
              spawn-protection = mkOption {
                type = int;
                default = 16;
              };
              sync-chunk-writes = mkOption {
                type = bool;
                default = true;
              };
              text-filtering-config = mkOption {
                type = str;
                default = "";
              };
              use-native-transport = mkOption {
                type = bool;
                default = true;
              };
              view-distance = mkOption {
                type = int.mkCheck (x: x >= 3 && x <= 32);
                default = 10;
              };
              white-list = mkOption {
                type = bool;
                default = false;
              };
            };
          };
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

          Restart = "on-failure";
          StandardOutput = "journal";
          StandardError = "journal";
          RemainAfterExit = "no";
        };
        preStart = ''
          cd ${cfg.dir}/${cfg.name}
          cp -r ${server} ./
        '';

        script = ''
          cd ${cfg.dir}/${cfg.name}
          ./start.sh
        '';
      };
    };
  }

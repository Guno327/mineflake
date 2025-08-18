{lib, ...}:
with lib; {
  serverProperties = mkOption {
    description = "Overrides for server.properties file";
    default = {};
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
            type = int;
            default = 100;
            apply = x: lib.asserts.assertMsg (x >= 10 && x <= 1000) "entity-broadcast-range must be in range 10-1000";
          };
          force-gamemode = mkOption {
            type = bool;
            default = false;
          };
          function-permission-level = mkOption {
            type = int;
            default = 2;
            apply = x: lib.asserts.assertMsg (x >= 1 && x <= 4) "function-permission-level must be in range 1-4";
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
            default = 60000;
          };
          max-world-size = mkOption {
            type = int;
            default = 29999984;
            apply = x: lib.asserts.assertMsg (x >= 1 && x <= 29999984) "max-world-size must be in range 1-29999984";
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
            type = int;
            default = 4;
            apply = x: lib.asserts.assertMsg (x >= 1 && x <= 4) "op-permission-level must be in range 1-4";
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
          "query.port" = mkOption {
            type = int;
            default = 25565;
          };
          rate-limit = mkOption {
            type = int;
            default = 0;
          };
          "rcon.password" = mkOption {
            type = str;
            default = "";
          };
          "rcon.port" = mkOption {
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
            type = int;
            default = 10;
            apply = x: lib.asserts.assertMsg (x >= 3 && x <= 32) "simultation-distance must be in range 3-32";
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
            type = int;
            default = 10;
            apply = x: lib.asserts.assertMsg (x >= 3 && x <= 32) "view-distance must be in range 3-32";
          };
          white-list = mkOption {
            type = bool;
            default = false;
          };
        };
      };
  };
}

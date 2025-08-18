{
  lib,
  pkgs,
  ...
}:
with lib; {
  enable = mkEnableOption "Enable Mineflake server";

  version = mkOption {
    type = types.str;
    description = "Server version, exact value depends on type of server";
  };

  dir = mkOption {
    type = types.path;
    default = "/var/lib/minecraft";
    description = "Directory to store server files";
  };

  name = lib.mkOption {
    type = lib.types.str;
    default = "server";
    description = "The name of this mineflake instance.";
  };

  flags = mkOption {
    type = types.str;
    default = "-Xms10G -Xmx10G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true";
    description = "Server launch flags";
  };

  java = mkOption {
    type = types.package;
    default = pkgs.jdk21;
    description = "Java package to use to run server";
  };

  # Legality reasons, make them type out true
  eula = mkOption {
    type = types.enum ["true" "false"];
    default = "false";
    description = "Whether to accept the EULA";
  };
}

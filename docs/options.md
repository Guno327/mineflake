# Standard Options

## `version`

- type: str
- default: "latest"
- description: Server version

## `dir`

- type: path
- default: `/var/lib/minecraft`
- description: Directory to store server files

## `name`

- type: str
- default: "server"
- description: The name of the instance

## `flags`

- type: str
- default: [aikars flags](https://docs.papermc.io/paper/aikars-flags/)
- description: Java launch flags

## `java`

- type: package
- default `pkgs.jdk21`
- description: Java package to run the server with

## `eula`

- type: str
- default: "false"
- description: Whether to accept the EULA

## `serverProperties`

- type: submodule
- default: {}
- description: Please see the Server Property options

# Server Properties

## Description

The options that are allowed in the server properties submodule are exactly the
same as those defined in `server.properties`. Please view the
[wiki](https://minecraft.fandom.com/wiki/Server.properties) for names, types,
limits, and default values.

## Example:

```nix
serverProperties = {
    allow-flight = true;
    difficulty = "hard";
    "rcon.port" = 25585;
    simulation-distance = 20;
};
```

## Synopsis

This project is a NixOS module that seeks to allow you to host the minecraft
server of your dreams. It currently has support for vanilla version, but FTB,
CurseForge, and Custom modpack support is in the works.

## McFetch

The main interesting part of this project is McFetch. It is the python script
that I am writting to fetch, index, and hash every modpack I can find and all of
its dependencies. At the core of NixOS is the idea that all builds should be
reproducible. In order to achieve this goal Nix is built around the core ideals
of functional programming, that being given the same inputs you will always
produce the same output (with little to no side-effects). This is only possible
if you can ensure that all of your build inputs are exactly the SAME. McFetch if
what is going to allow this module to produce these functionally pure minecraft
server derivations. It works by scrapping the web for modpack/version manifests,
reading through them, fetching all required files, then indexing and hashing
them. It then uses this database of files and dependencies to build the inputs
for a given modpack/version. This means at build time all fetched files can be
checked against the recorded hashes to make sure nothing has changed since the
script recorded them. While this does not protect against problems that arise
from the actual dependencies themselves, it allows us to limit the variables
that we are working with when having to debug a non-working server.

## Setup

For now this is just a standard flake module, there are plans for a stand-alone
docker image and web-ui to allow non-NixOS users to leverage the benefits of
functional, atomic builds on whatever system they are already using. For the
guide I am going to assume you are using a system flake:

### 1. Import Flake in `flake.nix`

```nix
inputs = {
    mineflake.url = "github:guno327/mineflake";
}

outputs = {
    mineflake,
}
```

### 2. Import Desired Modules (only vanilla currently)

```nix
nixosConfigurations.<name>.modules = [
    mineflake.nixosModules.vanilla
]
```

### 3. Configure Instance in `configuration.nix`

```nix
mineflake.vanilla = {
    enable = true;
    ...
}
```

Please view the options to see what you can configure

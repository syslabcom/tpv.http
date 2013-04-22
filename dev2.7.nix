{ }:

let
  base = import ./base.nix { };

in

with import <nixpkgs> {};

buildEnv {
  name = "dev-env";
  ignoreCollisions = true;
  paths =
    [ python27Packages.pyramid
      python27Packages.webtest
    ] ++ base.paths27;
}
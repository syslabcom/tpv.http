{ }:

let
  base = import ./base.nix { };

in

with import <nixpkgs> {};

buildEnv {
  name = "dev-env";
  ignoreCollisions = true;
  paths =
    [ python26Packages.pyramid
      python26Packages.webtest
    ] ++ base.paths26;
}
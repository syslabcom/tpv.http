{ python, pythonPackages, pythonDocs ? null }:

with import <nixpkgs> {};

let
  attrValues = lib.attrValues;
  optionals = lib.optionals;
  isPy26 = python.majorVersion == "2.6";
  isPy27 = python.majorVersion == "2.7";
in
{
  paths = [ python ] ++
          (optionals (pythonDocs != null) [ pythonDocs ]) ++
          (with pythonPackages;
           [
             coverage
             flake8
             ipdb
             ipdbplugin
             ipython
             nose
             pylint
             recursivePthLoader
             sqlite3
             virtualenv
           ] ++
           (optionals isPy26
            [
              unittest2
            ]) ++
           (optionals isPy27
            [ ])) ++
           attrValues python.modules;
}

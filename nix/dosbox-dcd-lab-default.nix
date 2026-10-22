let
  locked = (builtins.fromJSON (builtins.readFile ./flake.lock)).nodes.nixpkgs.locked;
  source = builtins.fetchTree { inherit (locked) type owner repo rev narHash; };
  pkgs = import source { system = "x86_64-linux"; };
in import ./dosbox-dcd-lab.nix { inherit pkgs; }

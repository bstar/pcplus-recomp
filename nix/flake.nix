{
  description = "PCPlus DOS binary analysis and reconstruction toolchain";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/f13ff45afd1bb73e640eaa08a7066dbed07e3238";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfreePredicate = pkg:
          nixpkgs.lib.hasPrefix "open-watcom" (nixpkgs.lib.getName pkg);
      };
      rea = pkgs.buildNpmPackage {
        pname = "pcplus-rea";
        version = "6.5.0";
        src = ./rea;
        nodejs = pkgs.nodejs_24;
        npmDepsHash = "sha256-Ua4i8Qz2xbHYgYjWq+D9PMAANU1h3VY6Nt0WuNDDRjI=";
        npmFlags = [ "--ignore-scripts" ];
        dontNpmBuild = true;
        nativeBuildInputs = [ pkgs.makeWrapper ];
        installPhase = ''
          runHook preInstall
          mkdir -p "$out/lib/pcplus-rea" "$out/bin"
          cp -r node_modules "$out/lib/pcplus-rea/"
          makeWrapper ${pkgs.nodejs_24}/bin/node "$out/bin/rea" \
            --add-flags "$out/lib/pcplus-rea/node_modules/rea-agents/scripts/rea.mjs" \
            --set GHIDRA_INSTALL_DIR ${pkgs.ghidra}/lib/ghidra \
            --set JAVA_HOME ${pkgs.jdk21} \
            --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.jdk21 ]}
          runHook postInstall
        '';
      };
      python = pkgs.python3.withPackages (ps: [ ps.unicorn ]);
    in {
      packages.${system} = {
        inherit rea;
        default = rea;
        watcom = pkgs.open-watcom-v2;
      };
      apps.${system}.rea = {
        type = "app";
        program = "${rea}/bin/rea";
        meta.description = "REA CLI and stdio MCP with pinned Ghidra and Java";
      };
      checks.${system}.dos-compiler = pkgs.runCommand "pcplus-dos-compiler-check" {
        nativeBuildInputs = [ pkgs.open-watcom-v2 pkgs.file ];
      } ''
        cat > probe.c <<'EOF'
        #include <stdio.h>
        int main(void) { puts("PCPlus DOS toolchain check"); return 0; }
        EOF
        wcl -q -bt=dos -0 -ms -fe=probe.exe probe.c
        file probe.exe | grep 'MS-DOS executable'
        mkdir -p "$out"
        cp probe.exe "$out/"
      '';
      devShells.${system} = {
        analysis = pkgs.mkShell {
          packages = [ rea python pkgs.jq pkgs.nasm pkgs.lhasa ];
        };
        default = pkgs.mkShell {
          packages = with pkgs; [
            rea ghidra jdk21 nodejs_24
            open-watcom-v2 nasm gnumake binutils file
            dosbox-x mtools jq lhasa
          ] ++ [ python ];
          GHIDRA_INSTALL_DIR = "${pkgs.ghidra}/lib/ghidra";
          JAVA_HOME = "${pkgs.jdk21}";
          # DOS headers, not the Linux headers selected by the generic wrapper.
          WATCOM = "${pkgs.open-watcom-v2.unwrapped}";
          INCLUDE = "${pkgs.open-watcom-v2.unwrapped}/h";
        };
      };
    };
}

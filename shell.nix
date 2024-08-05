{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = [
    pkgs.jq
    pkgs.ruff-lsp
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.nodejs_22
    pkgs.nodePackages.pnpm
    pkgs.nodePackages.yarn
    pkgs.nodePackages.vscode-json-languageserver
  ];

  shellHook = ''
    test -d venv || python -m venv venv
    source venv/bin/activate
    export PATH=$PATH:$(pwd)/venv/bin
  '';
}

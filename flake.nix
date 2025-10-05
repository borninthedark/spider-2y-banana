{
  description = "Fedora Exousia bootc image with K8s tools, Sway, and virtualization";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Fedora bootc base image configuration
        fedoraVersion = "42";
        registryUsername = builtins.getEnv "REGISTRY_USERNAME";
        imageName = "fedora-exousia";
        registry = "docker.io";

        # Pull fedora-bootc base image
        fedoraBootcBase = pkgs.dockerTools.pullImage {
          imageName = "quay.io/fedora/fedora-bootc";
          imageDigest = "sha256:8a6e3b7f5c4d2a9b1e0f3c6d8e7f9a2b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f";
          sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";  # Update with actual hash
          finalImageTag = fedoraVersion;
        };

        # Create container image
        containerImage = pkgs.dockerTools.buildImage {
          name = "${registry}/${registryUsername}/${imageName}";
          tag = "latest";

          fromImage = fedoraBootcBase;

          # Copy Ansible playbooks and scripts into the build context
          copyToRoot = pkgs.buildEnv {
            name = "exousia-build-context";
            paths = [
              (pkgs.runCommand "ansible-content" {} ''
                mkdir -p $out
                cp -r ${./ansible} $out/ansible
                cp -r ${./custom-scripts} $out/custom-scripts
              '')
            ];
          };

          config = {
            Env = [
              "CONTAINER=docker"
              "K3S_VERSION=v1.30.5+k3s1"
              "KUBECTL_VERSION=v1.30.0"
            ];

            Labels = {
              "org.opencontainers.image.title" = "fedora-exousia";
              "org.opencontainers.image.description" = "Fedora Exousia bootc image with K8s tools, Sway, and virtualization";
              "org.opencontainers.image.licenses" = "MIT";
              "org.opencontainers.image.source" = "https://github.com/borninthedark/spider-2y-banana";
              "maintainer" = "spider-2y-banana";
              "version" = fedoraVersion;
            };
          };

          # Run Ansible provisioning during image build
          runAsRoot = ''
            #!${pkgs.runtimeShell}
            set -e

            # Install Ansible if not present
            if ! command -v ansible-playbook &> /dev/null; then
              if command -v dnf5 &> /dev/null; then
                dnf5 install -y ansible-core
              else
                dnf install -y ansible-core
              fi
            fi

            # Run provisioning playbook
            cd /ansible
            ansible-playbook \
              --connection=local \
              --inventory=localhost, \
              --extra-vars "fedora_version=${fedoraVersion}" \
              --extra-vars "enable_plymouth=true" \
              --extra-vars "enable_k8s_tools=true" \
              --extra-vars "enable_virtualization=true" \
              --extra-vars "enable_sway_desktop=true" \
              --extra-vars "enable_graphical_target=true" \
              --extra-vars "enable_greetd=true" \
              --extra-vars "enable_rpmfusion_ostree=false" \
              playbooks/provision.yml

            # Cleanup
            if command -v dnf5 &> /dev/null; then
              dnf5 clean all
            else
              dnf clean all
            fi
            rm -rf /tmp/* /var/tmp/* /var/cache/dnf /var/cache/libdnf5 2>/dev/null || true
          '';
        };

      in {
        packages = {
          container = containerImage;
          default = containerImage;
        };

        # Development shell with required tools
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            ansible
            ansible-lint
            python311
            python311Packages.pip
            podman
            buildah
            skopeo
          ];

          shellHook = ''
            echo "Fedora Exousia development environment"
            echo "Available commands:"
            echo "  nix build .#container    - Build container image"
            echo "  ansible-playbook         - Run Ansible playbooks"
            echo "  podman/buildah           - Container tools"
          '';
        };
      }
    );
}

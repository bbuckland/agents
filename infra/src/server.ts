import * as pulumi from "@pulumi/pulumi";
import * as hcloud from "@pulumi/hcloud";
import { serverConfig } from "./config";
import { generateCloudInit, CloudInitParams } from "./cloud-init";

export interface ServerOutputs {
  serverId: pulumi.Output<number>;
  serverName: pulumi.Output<string>;
  ipv4Address: pulumi.Output<string>;
  ipv6Address: pulumi.Output<string>;
}

export function createServer(cloudInitParams: CloudInitParams): ServerOutputs {
  // Create SSH key resource
  const sshKey = new hcloud.SshKey("openclaw-ssh-key", {
    name: "openclaw-deploy-key",
    publicKey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDjcfBksKxpPQMoiw7zq1OvBiQHJM97WlfgnXCv3EZjB buckbot",
  });

  // Generate cloud-init user data
  const userData = generateCloudInit(cloudInitParams);

  // Create the server
  const server = new hcloud.Server("openclaw-gateway", {
    name: serverConfig.name,
    serverType: serverConfig.serverType,
    location: serverConfig.location,
    image: serverConfig.image,
    sshKeys: [sshKey.id],
    userData: userData,
    publicNets: [{
      ipv4Enabled: true,
      ipv6Enabled: true,
    }],
    labels: {
      environment: "production",
      service: "openclaw-gateway",
      managed_by: "pulumi",
    },
  });

  // Create firewall (defense in depth - in addition to UFW)
  const firewall = new hcloud.Firewall("openclaw-firewall", {
    name: "openclaw-gateway-fw",
    rules: [
      {
        direction: "in",
        protocol: "tcp",
        port: "22",
        sourceIps: ["0.0.0.0/0", "::/0"],
        description: "SSH access",
      },
      {
        direction: "in",
        protocol: "icmp",
        sourceIps: ["0.0.0.0/0", "::/0"],
        description: "ICMP ping",
      },
      // Note: Port 18789 intentionally NOT allowed
      // Access via Tailscale only
    ],
    labels: {
      environment: "production",
      service: "openclaw-gateway",
    },
  });

  // Attach firewall to server
  new hcloud.FirewallAttachment("openclaw-fw-attachment", {
    firewallId: firewall.id.apply(id => parseInt(id)),
    serverIds: [server.id.apply(id => parseInt(id))],
  });

  return {
    serverId: server.id.apply(id => parseInt(id)),
    serverName: server.name,
    ipv4Address: server.ipv4Address,
    ipv6Address: server.ipv6Address,
  };
}

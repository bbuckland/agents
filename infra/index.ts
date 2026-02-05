import * as pulumi from "@pulumi/pulumi";
import { secrets } from "./src/config";
import { createServer } from "./src/server";

// Create the OpenClaw gateway server
const serverOutputs = createServer({
  gatewayToken: secrets.gatewayToken,
  anthropicApiKey: secrets.anthropicApiKey,
  githubToken: secrets.githubToken,
  ynabApiKey: secrets.ynabApiKey,
  telegramBuckbot: secrets.telegramBuckbot,
  telegramExpense: secrets.telegramExpense,
  telegramQuant: secrets.telegramQuant,
  tailscaleAuthKey: secrets.tailscaleAuthKey,
});

// Export outputs for reference
export const serverId = serverOutputs.serverId;
export const serverName = serverOutputs.serverName;
export const ipv4Address = serverOutputs.ipv4Address;
export const ipv6Address = serverOutputs.ipv6Address;

// Tailscale hostname (manual - will need to be updated after first deploy)
export const tailscaleHostname = pulumi.output("openclaw-gateway.tailXXXXX.ts.net");

// Security reminder
export const securityNote = pulumi.output(
  "Gateway is accessible via Tailscale only. Run verification commands after deploy."
);

import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const openclawConfig = new pulumi.Config("openclaw");
const anthropicConfig = new pulumi.Config("anthropic");
const githubConfig = new pulumi.Config("github");
const ynabConfig = new pulumi.Config("ynab");
const telegramConfig = new pulumi.Config("telegram");
const tailscaleConfig = new pulumi.Config("tailscale");

export const secrets = {
  gatewayToken: openclawConfig.requireSecret("gatewayToken"),
  anthropicApiKey: anthropicConfig.requireSecret("apiKey"),
  githubToken: githubConfig.requireSecret("token"),
  ynabApiKey: ynabConfig.requireSecret("apiKey"),
  telegramBuckbot: telegramConfig.requireSecret("buckbotToken"),
  telegramExpense: telegramConfig.requireSecret("expenseToken"),
  telegramQuant: telegramConfig.requireSecret("quantToken"),
  tailscaleAuthKey: tailscaleConfig.requireSecret("authKey"),
};

export const serverConfig = {
  name: config.get("serverName") || "openclaw-gateway",
  location: config.get("location") || "fsn1", // Falkenstein, Germany
  serverType: config.get("serverType") || "cx22", // 2 vCPU, 4GB RAM
  image: config.get("image") || "ubuntu-24.04",
};

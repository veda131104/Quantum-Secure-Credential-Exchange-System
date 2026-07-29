const CredentialRegistry = artifacts.require("CredentialRegistry");
const fs = require("fs");

module.exports = function (deployer, network, accounts) {
  deployer.deploy(CredentialRegistry).then(() => {
    console.log("CredentialRegistry deployed to:", CredentialRegistry.address);
    console.log("Deployed by:", accounts[0]);

    // Save deployment info
    const deploymentInfo = {
      contractAddress: CredentialRegistry.address,
      deployer: accounts[0],
      network: network,
      deployedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      "./deployment-info.json",
      JSON.stringify(deploymentInfo, null, 2)
    );

    console.log("Deployment info saved to deployment-info.json");

    // Save ABI
    const artifact = require("../build/contracts/CredentialRegistry.json");
    fs.writeFileSync(
      "./CredentialRegistry-ABI.json",
      JSON.stringify(artifact.abi, null, 2)
    );

    console.log("ABI saved to CredentialRegistry-ABI.json");
  });
};

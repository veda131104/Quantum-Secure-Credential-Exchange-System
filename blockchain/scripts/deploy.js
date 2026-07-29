// Deployment script for CredentialRegistry contract
const hre = require("hardhat");

async function main() {
  console.log("Deploying CredentialRegistry contract...");

  // Get the contract factory
  const CredentialRegistry = await hre.ethers.getContractFactory("CredentialRegistry");

  // Deploy the contract
  const credentialRegistry = await CredentialRegistry.deploy();

  await credentialRegistry.deployed();

  console.log("CredentialRegistry deployed to:", credentialRegistry.address);

  // Get deployer address
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployed by:", deployer.address);

  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    contractAddress: credentialRegistry.address,
    deployer: deployer.address,
    network: hre.network.name,
    deployedAt: new Date().toISOString(),
  };

  fs.writeFileSync(
    "./deployment-info.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("Deployment info saved to deployment-info.json");

  // Save ABI
  const artifact = await hre.artifacts.readArtifact("CredentialRegistry");
  fs.writeFileSync(
    "./CredentialRegistry-ABI.json",
    JSON.stringify(artifact.abi, null, 2)
  );

  console.log("ABI saved to CredentialRegistry-ABI.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

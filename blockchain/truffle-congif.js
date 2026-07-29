module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*", // Match any network id
    },
    localhost: {
      host: "127.0.0.1",
      port: 8545,
      network_id: 1337,
    },
    ganache: {
      host: "127.0.0.1",
      port: 8545,
      network_id: 1337,
    },
  },

  // Configure your compilers
  compilers: {
    solc: {
      version: "0.8.19",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200,
        },
      },
    },
  },

  // Set default mocha options
  mocha: {
    timeout: 100000
  },

  // Configure directories
  contracts_directory: "./contracts",
  contracts_build_directory: "./build/contracts",
  migrations_directory: "./migrations",
  test_directory: "./test",
};

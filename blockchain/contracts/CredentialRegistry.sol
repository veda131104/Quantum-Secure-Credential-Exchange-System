// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title CredentialRegistry
 * @dev Smart contract for managing digital credentials with PQC signatures
 */
contract CredentialRegistry {
    address public admin;

    struct Issuer {
        bool exists;
        string name;
        string pqcPublicKey;
        bool isActive;
        uint256 registeredAt;
    }

    struct Credential {
        bool exists;
        address userAddress;
        address issuerAddress;
        string ipfsCID;
        string credentialHash;
        string pqcSignature;
        uint256 timestamp;
        bool isRevoked;
    }

    // Mappings
    mapping(address => Issuer) public issuers;
    mapping(string => Credential) public credentials; // credentialId => Credential
    mapping(address => string[]) public userCredentials; // user => credential IDs
    mapping(address => string[]) public issuerCredentials; // issuer => credential IDs

    // Events
    event IssuerRegistered(
        address indexed issuerAddress,
        string name,
        string pqcPublicKey
    );
    event IssuerDeactivated(address indexed issuerAddress);
    event CredentialIssued(
        string indexed credentialId,
        address indexed userAddress,
        address indexed issuerAddress,
        string ipfsCID
    );
    event CredentialRevoked(
        string indexed credentialId,
        address indexed issuerAddress
    );

    // Modifiers
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    modifier onlyActiveIssuer() {
        require(
            issuers[msg.sender].exists && issuers[msg.sender].isActive,
            "Only active issuer can call this function"
        );
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    /**
     * @dev Register a new issuer
     */
    function registerIssuer(
        address issuerAddress,
        string memory name,
        string memory pqcPublicKey
    ) public onlyAdmin {
        require(!issuers[issuerAddress].exists, "Issuer already registered");

        issuers[issuerAddress] = Issuer({
            exists: true,
            name: name,
            pqcPublicKey: pqcPublicKey,
            isActive: true,
            registeredAt: block.timestamp
        });

        emit IssuerRegistered(issuerAddress, name, pqcPublicKey);
    }

    /**
     * @dev Deactivate an issuer
     */
    function deactivateIssuer(address issuerAddress) public onlyAdmin {
        require(issuers[issuerAddress].exists, "Issuer not found");
        issuers[issuerAddress].isActive = false;
        emit IssuerDeactivated(issuerAddress);
    }

    /**
     * @dev Reactivate an issuer
     */
    function reactivateIssuer(address issuerAddress) public onlyAdmin {
        require(issuers[issuerAddress].exists, "Issuer not found");
        issuers[issuerAddress].isActive = true;
    }

    /**
     * @dev Register a new credential
     */
    function registerCredential(
        string memory credentialId,
        address userAddress,
        string memory ipfsCID,
        string memory credentialHash,
        string memory pqcSignature
    ) public onlyActiveIssuer {
        require(!credentials[credentialId].exists, "Credential already exists");
        require(userAddress != address(0), "Invalid user address");

        credentials[credentialId] = Credential({
            exists: true,
            userAddress: userAddress,
            issuerAddress: msg.sender,
            ipfsCID: ipfsCID,
            credentialHash: credentialHash,
            pqcSignature: pqcSignature,
            timestamp: block.timestamp,
            isRevoked: false
        });

        userCredentials[userAddress].push(credentialId);
        issuerCredentials[msg.sender].push(credentialId);

        emit CredentialIssued(credentialId, userAddress, msg.sender, ipfsCID);
    }

    /**
     * @dev Revoke a credential
     */
    function revokeCredential(string memory credentialId)
        public
        onlyActiveIssuer
    {
        require(credentials[credentialId].exists, "Credential not found");
        require(
            credentials[credentialId].issuerAddress == msg.sender,
            "Only issuer can revoke their credential"
        );
        require(
            !credentials[credentialId].isRevoked,
            "Credential already revoked"
        );

        credentials[credentialId].isRevoked = true;
        emit CredentialRevoked(credentialId, msg.sender);
    }

    /**
     * @dev Get credential details
     */
    function getCredential(string memory credentialId)
        public
        view
        returns (
            bool exists,
            address userAddress,
            address issuerAddress,
            string memory ipfsCID,
            string memory credentialHash,
            string memory pqcSignature,
            uint256 timestamp,
            bool isRevoked
        )
    {
        Credential memory cred = credentials[credentialId];
        return (
            cred.exists,
            cred.userAddress,
            cred.issuerAddress,
            cred.ipfsCID,
            cred.credentialHash,
            cred.pqcSignature,
            cred.timestamp,
            cred.isRevoked
        );
    }

    /**
     * @dev Get issuer details
     */
    function getIssuer(address issuerAddress)
        public
        view
        returns (
            bool exists,
            string memory name,
            string memory pqcPublicKey,
            bool isActive,
            uint256 registeredAt
        )
    {
        Issuer memory issuer = issuers[issuerAddress];
        return (
            issuer.exists,
            issuer.name,
            issuer.pqcPublicKey,
            issuer.isActive,
            issuer.registeredAt
        );
    }

    /**
     * @dev Get user's credential IDs
     */
    function getUserCredentials(address userAddress)
        public
        view
        returns (string[] memory)
    {
        return userCredentials[userAddress];
    }

    /**
     * @dev Get issuer's credential IDs
     */
    function getIssuerCredentials(address issuerAddress)
        public
        view
        returns (string[] memory)
    {
        return issuerCredentials[issuerAddress];
    }

    /**
     * @dev Get total credentials count for a user
     */
    function getUserCredentialCount(address userAddress)
        public
        view
        returns (uint256)
    {
        return userCredentials[userAddress].length;
    }

    /**
     * @dev Get total credentials issued by an issuer
     */
    function getIssuerCredentialCount(address issuerAddress)
        public
        view
        returns (uint256)
    {
        return issuerCredentials[issuerAddress].length;
    }

    /**
     * @dev Verify if credential is valid (exists and not revoked)
     */
    function isCredentialValid(string memory credentialId)
        public
        view
        returns (bool)
    {
        return
            credentials[credentialId].exists &&
            !credentials[credentialId].isRevoked;
    }

    /**
     * @dev Transfer admin rights
     */
    function transferAdmin(address newAdmin) public onlyAdmin {
        require(newAdmin != address(0), "Invalid address");
        admin = newAdmin;
    }
}

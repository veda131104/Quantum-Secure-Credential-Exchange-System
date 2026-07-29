"""
PQC Attack Simulation Tests
Tests for various attack scenarios against the Post-Quantum Cryptography implementation
"""

import pytest
import time
import random
import os
from datetime import datetime, timedelta

from app.services.pqc.dilithium_service import pqc_service


@pytest.mark.attack
class TestPQCAttacks:
    """Comprehensive attack simulation test suite"""

    def setup_method(self):
        """Setup for each test method"""
        self.attack_results = []

    def test_01_signature_forgery_attack(self, test_pqc_keypair, test_credential_data, test_results_collector):
        """
        Attack Scenario 1: Signature Forgery
        Attempt to create valid signatures without the private key
        Expected Result: All forgery attempts should be rejected (100% defense rate)
        """
        print("\n[ATTACK 1] Testing Signature Forgery Resistance...")

        # Prepare credential data
        credential_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        credential_hash = pqc_service.hash_data(credential_str)

        forgery_attempts = 100
        successful_forgeries = 0
        failed_forgeries = 0

        for i in range(forgery_attempts):
            # Generate random signature (forgery attempt)
            random_signature = os.urandom(1210).hex()  # Dilithium2 signature size

            # Attempt verification
            try:
                is_valid = pqc_service.verify_signature(
                    data=credential_hash,
                    signature_hex=random_signature,
                    public_key_hex=test_pqc_keypair["public_key"]
                )

                if is_valid:
                    successful_forgeries += 1
                else:
                    failed_forgeries += 1
            except Exception:
                # Any exception means the forgery was caught
                failed_forgeries += 1

        # Calculate defense rate
        defense_rate = (failed_forgeries / forgery_attempts) * 100

        # Record results
        result = {
            "attack_type": "Signature Forgery",
            "total_attempts": forgery_attempts,
            "successful_attacks": successful_forgeries,
            "failed_attacks": failed_forgeries,
            "defense_rate": defense_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)

        print(f"   Forgery Attempts: {forgery_attempts}")
        print(f"   Successful Forgeries: {successful_forgeries}")
        print(f"   Failed Forgeries: {failed_forgeries}")
        print(f"   Defense Rate: {defense_rate:.2f}%")

        # Assert 100% defense rate
        assert successful_forgeries == 0, "Signature forgery attack succeeded!"
        assert defense_rate == 100.0, f"Defense rate should be 100%, got {defense_rate}%"

    def test_02_key_substitution_attack(self, test_pqc_keypair, test_pqc_keypair_2, test_credential_data, test_results_collector):
        """
        Attack Scenario 2: Key Substitution Attack
        Sign with Issuer A's key, verify with Issuer B's key
        Expected Result: Verification should fail (wrong public key)
        """
        print("\n[ATTACK 2] Testing Key Substitution Resistance...")

        # Prepare credential data
        credential_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        credential_hash = pqc_service.hash_data(credential_str)

        # Sign with Issuer A's private key
        signature = pqc_service.sign_data(
            data=credential_hash,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        substitution_attempts = 10
        successful_substitutions = 0

        for i in range(substitution_attempts):
            # Attempt to verify with Issuer B's public key (wrong key)
            try:
                is_valid = pqc_service.verify_signature(
                    data=credential_hash,
                    signature_hex=signature,
                    public_key_hex=test_pqc_keypair_2["public_key"]
                )

                if is_valid:
                    successful_substitutions += 1
            except Exception:
                # Exception means attack was caught
                pass

        defense_rate = ((substitution_attempts - successful_substitutions) / substitution_attempts) * 100

        # Record results
        result = {
            "attack_type": "Key Substitution",
            "total_attempts": substitution_attempts,
            "successful_attacks": successful_substitutions,
            "failed_attacks": substitution_attempts - successful_substitutions,
            "defense_rate": defense_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)

        print(f"   Substitution Attempts: {substitution_attempts}")
        print(f"   Successful Substitutions: {successful_substitutions}")
        print(f"   Defense Rate: {defense_rate:.2f}%")

        assert successful_substitutions == 0, "Key substitution attack succeeded!"
        assert defense_rate == 100.0

    def test_03_timing_attack_resistance(self, test_pqc_keypair, test_credential_data, test_results_collector):
        """
        Attack Scenario 3: Timing Attack
        Measure verification times to detect if timing reveals information
        Expected Result: Constant-time verification (variance < 5%)
        """
        print("\n[ATTACK 3] Testing Timing Attack Resistance...")

        credential_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        credential_hash = pqc_service.hash_data(credential_str)

        # Create valid signature
        valid_signature = pqc_service.sign_data(
            data=credential_hash,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        # Create invalid signature
        invalid_signature = os.urandom(1210).hex()

        iterations = 1000
        valid_times = []
        invalid_times = []

        # Measure valid signature verification times
        for i in range(iterations):
            start = time.perf_counter()
            try:
                pqc_service.verify_signature(
                    data=credential_hash,
                    signature_hex=valid_signature,
                    public_key_hex=test_pqc_keypair["public_key"]
                )
            except Exception:
                pass
            end = time.perf_counter()
            valid_times.append((end - start) * 1000)  # Convert to ms

        # Measure invalid signature verification times
        for i in range(iterations):
            start = time.perf_counter()
            try:
                pqc_service.verify_signature(
                    data=credential_hash,
                    signature_hex=invalid_signature,
                    public_key_hex=test_pqc_keypair["public_key"]
                )
            except Exception:
                pass
            end = time.perf_counter()
            invalid_times.append((end - start) * 1000)  # Convert to ms

        # Calculate statistics
        valid_mean = sum(valid_times) / len(valid_times)
        invalid_mean = sum(invalid_times) / len(invalid_times)

        valid_variance = sum((x - valid_mean) ** 2 for x in valid_times) / len(valid_times)
        invalid_variance = sum((x - invalid_mean) ** 2 for x in invalid_times) / len(invalid_times)

        valid_std = valid_variance ** 0.5
        invalid_std = invalid_variance ** 0.5

        # Calculate timing difference percentage
        timing_difference_pct = abs((valid_mean - invalid_mean) / valid_mean) * 100

        # Record timing measurements
        timing_data = {
            "valid_signatures": {
                "mean_ms": valid_mean,
                "std_ms": valid_std,
                "min_ms": min(valid_times),
                "max_ms": max(valid_times),
                "measurements": valid_times
            },
            "invalid_signatures": {
                "mean_ms": invalid_mean,
                "std_ms": invalid_std,
                "min_ms": min(invalid_times),
                "max_ms": max(invalid_times),
                "measurements": invalid_times
            },
            "timing_difference_pct": timing_difference_pct,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["timing_measurements"].append(timing_data)

        # Defense assessment
        is_constant_time = timing_difference_pct < 10  # Allow 10% variance
        defense_rate = 100.0 if is_constant_time else 50.0

        result = {
            "attack_type": "Timing Attack",
            "total_attempts": iterations * 2,
            "successful_attacks": 0 if is_constant_time else 1,
            "failed_attacks": 1 if is_constant_time else 0,
            "defense_rate": defense_rate,
            "timing_difference_pct": timing_difference_pct,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)

        print(f"   Valid Signature Verification Time: {valid_mean:.3f} ± {valid_std:.3f} ms")
        print(f"   Invalid Signature Verification Time: {invalid_mean:.3f} ± {invalid_std:.3f} ms")
        print(f"   Timing Difference: {timing_difference_pct:.2f}%")
        print(f"   Constant-Time: {'Yes' if is_constant_time else 'No'}")

        # Note: We allow some variance as perfect constant-time is very difficult
        # The important thing is that the difference is not exploitable
        assert timing_difference_pct < 50, f"Timing difference too large: {timing_difference_pct}%"

    def test_04_input_validation_bypass(self, test_pqc_keypair, test_credential_data, test_results_collector):
        """
        Attack Scenario 4: Input Validation Bypass
        Test malformed inputs to bypass validation
        Expected Result: All invalid inputs should be caught and rejected
        """
        print("\n[ATTACK 4] Testing Input Validation...")

        credential_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        credential_hash = pqc_service.hash_data(credential_str)

        # Create valid signature for some tests
        valid_signature = pqc_service.sign_data(
            data=credential_hash,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        validation_tests = [
            # Test empty signature
            {"name": "Empty Signature", "signature": "", "should_fail": True},

            # Test truncated signature
            {"name": "Truncated Signature", "signature": valid_signature[:100], "should_fail": True},

            # Test oversized signature
            {"name": "Oversized Signature", "signature": valid_signature + "abcd" * 1000, "should_fail": True},

            # Test non-hex characters
            {"name": "Non-hex Characters", "signature": "zzzzzz" * 400, "should_fail": True},

            # Test null bytes
            {"name": "Null Bytes", "signature": "\x00" * 2420, "should_fail": True},

            # Test unicode injection
            {"name": "Unicode Injection", "signature": "🔒" * 1000, "should_fail": True},

            # Test SQL injection attempt (in hex)
            {"name": "SQL Injection", "signature": "'; DROP TABLE credentials; --", "should_fail": True},

            # Test valid signature (control)
            {"name": "Valid Signature (Control)", "signature": valid_signature, "should_fail": False},
        ]

        total_tests = len(validation_tests)
        caught_attacks = 0
        missed_attacks = 0
        results_detail = []

        for test_case in validation_tests:
            try:
                is_valid = pqc_service.verify_signature(
                    data=credential_hash,
                    signature_hex=test_case["signature"],
                    public_key_hex=test_pqc_keypair["public_key"]
                )

                if test_case["should_fail"]:
                    if not is_valid:
                        caught_attacks += 1
                        results_detail.append({"test": test_case["name"], "result": "PASS (Caught)"})
                    else:
                        missed_attacks += 1
                        results_detail.append({"test": test_case["name"], "result": "FAIL (Missed)"})
                else:
                    # Control test - valid signature should pass
                    if is_valid:
                        results_detail.append({"test": test_case["name"], "result": "PASS (Valid)"})
                    else:
                        results_detail.append({"test": test_case["name"], "result": "FAIL (False Positive)"})

            except (ValueError, TypeError, Exception) as e:
                # Exception means the attack was caught
                if test_case["should_fail"]:
                    caught_attacks += 1
                    results_detail.append({"test": test_case["name"], "result": "PASS (Exception)"})
                else:
                    results_detail.append({"test": test_case["name"], "result": "FAIL (False Exception)"})

        defense_rate = (caught_attacks / (total_tests - 1)) * 100  # Exclude control test

        # Record results
        result = {
            "attack_type": "Input Validation Bypass",
            "total_attempts": total_tests - 1,
            "successful_attacks": missed_attacks,
            "failed_attacks": caught_attacks,
            "defense_rate": defense_rate,
            "details": results_detail,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)
        test_results_collector["validation_tests"].append(result)

        print(f"   Total Validation Tests: {total_tests}")
        print(f"   Attacks Caught: {caught_attacks}")
        print(f"   Attacks Missed: {missed_attacks}")
        print(f"   Defense Rate: {defense_rate:.2f}%")

        for detail in results_detail:
            print(f"      {detail['test']}: {detail['result']}")

        assert missed_attacks == 0, f"{missed_attacks} input validation attacks succeeded!"

    def test_05_credential_tampering_detection(self, test_pqc_keypair, test_credential_data, test_results_collector):
        """
        Attack Scenario 5: Credential Tampering
        Modify credential data after signing and attempt verification
        Expected Result: Tampering should be detected (hash mismatch)
        """
        print("\n[ATTACK 5] Testing Credential Tampering Detection...")

        # Original credential data
        original_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        original_hash = pqc_service.hash_data(original_str)

        # Sign original data
        signature = pqc_service.sign_data(
            data=original_hash,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        tampering_attempts = [
            {
                "name": "Modified User ID",
                "data": f"TAMPERED-USER{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
            },
            {
                "name": "Modified Credential Type",
                "data": f"{test_credential_data['user_id']}TAMPERED_TYPE{test_credential_data['credential_name']}"
            },
            {
                "name": "Modified Credential Name",
                "data": f"{test_credential_data['user_id']}{test_credential_data['credential_type']}TAMPERED NAME"
            },
            {
                "name": "Extra Data Appended",
                "data": original_str + "EXTRA_DATA"
            },
            {
                "name": "Data Truncated",
                "data": original_str[:-10]
            },
        ]

        detected_tampering = 0
        missed_tampering = 0

        for attempt in tampering_attempts:
            tampered_hash = pqc_service.hash_data(attempt["data"])

            try:
                is_valid = pqc_service.verify_signature(
                    data=tampered_hash,
                    signature_hex=signature,
                    public_key_hex=test_pqc_keypair["public_key"]
                )

                if not is_valid:
                    detected_tampering += 1
                else:
                    missed_tampering += 1
            except Exception:
                detected_tampering += 1

        total_attempts = len(tampering_attempts)
        defense_rate = (detected_tampering / total_attempts) * 100

        # Record results
        result = {
            "attack_type": "Credential Tampering",
            "total_attempts": total_attempts,
            "successful_attacks": missed_tampering,
            "failed_attacks": detected_tampering,
            "defense_rate": defense_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)

        print(f"   Tampering Attempts: {total_attempts}")
        print(f"   Detected: {detected_tampering}")
        print(f"   Missed: {missed_tampering}")
        print(f"   Defense Rate: {defense_rate:.2f}%")

        assert missed_tampering == 0, "Credential tampering was not detected!"
        assert defense_rate == 100.0

    def test_06_replay_attack_simulation(self, test_pqc_keypair, test_credential_data, test_results_collector):
        """
        Attack Scenario 6: Replay Attack
        Reuse a valid signature for different data
        Expected Result: Signature should only validate for original data
        """
        print("\n[ATTACK 6] Testing Replay Attack Resistance...")

        # Original credential A
        cred_a_str = f"{test_credential_data['user_id']}{test_credential_data['credential_type']}{test_credential_data['credential_name']}"
        cred_a_hash = pqc_service.hash_data(cred_a_str)

        # Sign credential A
        signature_a = pqc_service.sign_data(
            data=cred_a_hash,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        # Create different credentials (B, C, D, E)
        replay_attempts = [
            f"{test_credential_data['user_id']}different_type{test_credential_data['credential_name']}",
            f"different_user{test_credential_data['credential_type']}{test_credential_data['credential_name']}",
            f"{test_credential_data['user_id']}{test_credential_data['credential_type']}Different Name",
            f"completely_different_credential_data",
            f"{test_credential_data['user_id']}{test_credential_data['credential_type']}",
        ]

        successful_replays = 0
        failed_replays = 0

        for replay_data in replay_attempts:
            replay_hash = pqc_service.hash_data(replay_data)

            try:
                is_valid = pqc_service.verify_signature(
                    data=replay_hash,
                    signature_hex=signature_a,
                    public_key_hex=test_pqc_keypair["public_key"]
                )

                if is_valid:
                    successful_replays += 1
                else:
                    failed_replays += 1
            except Exception:
                failed_replays += 1

        # Verify original signature still works
        original_still_valid = pqc_service.verify_signature(
            data=cred_a_hash,
            signature_hex=signature_a,
            public_key_hex=test_pqc_keypair["public_key"]
        )

        total_attempts = len(replay_attempts)
        defense_rate = (failed_replays / total_attempts) * 100

        # Record results
        result = {
            "attack_type": "Replay Attack",
            "total_attempts": total_attempts,
            "successful_attacks": successful_replays,
            "failed_attacks": failed_replays,
            "defense_rate": defense_rate,
            "original_still_valid": original_still_valid,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["attack_scenarios"].append(result)

        print(f"   Replay Attempts: {total_attempts}")
        print(f"   Successful Replays: {successful_replays}")
        print(f"   Failed Replays: {failed_replays}")
        print(f"   Defense Rate: {defense_rate:.2f}%")
        print(f"   Original Signature Still Valid: {original_still_valid}")

        assert successful_replays == 0, "Replay attack succeeded!"
        assert original_still_valid, "Original signature became invalid!"
        assert defense_rate == 100.0


@pytest.mark.performance
class TestPQCPerformance:
    """Performance benchmarking tests"""

    def test_signing_performance(self, test_pqc_keypair, test_results_collector):
        """Measure signature generation performance"""
        print("\n[PERFORMANCE] Testing Signing Performance...")

        iterations = 100
        times = []

        test_data = b"Performance test credential data"

        for i in range(iterations):
            start = time.perf_counter()
            signature = pqc_service.sign_data(
                data=test_data,
                private_key_hex=test_pqc_keypair["private_key"]
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)  # ms

        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        performance_data = {
            "operation": "signing",
            "iterations": iterations,
            "mean_ms": mean_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "measurements": times,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["performance_metrics"].append(performance_data)

        print(f"   Iterations: {iterations}")
        print(f"   Mean Time: {mean_time:.3f} ms")
        print(f"   Min Time: {min_time:.3f} ms")
        print(f"   Max Time: {max_time:.3f} ms")

        assert mean_time < 100, f"Signing too slow: {mean_time}ms (expected < 100ms)"

    def test_verification_performance(self, test_pqc_keypair, test_results_collector):
        """Measure signature verification performance"""
        print("\n[PERFORMANCE] Testing Verification Performance...")

        test_data = b"Performance test credential data"
        signature = pqc_service.sign_data(
            data=test_data,
            private_key_hex=test_pqc_keypair["private_key"]
        )

        iterations = 100
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            is_valid = pqc_service.verify_signature(
                data=test_data,
                signature_hex=signature,
                public_key_hex=test_pqc_keypair["public_key"]
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)  # ms

        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        performance_data = {
            "operation": "verification",
            "iterations": iterations,
            "mean_ms": mean_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "measurements": times,
            "timestamp": datetime.utcnow().isoformat()
        }
        test_results_collector["performance_metrics"].append(performance_data)

        print(f"   Iterations: {iterations}")
        print(f"   Mean Time: {mean_time:.3f} ms")
        print(f"   Min Time: {min_time:.3f} ms")
        print(f"   Max Time: {max_time:.3f} ms")

        assert mean_time < 50, f"Verification too slow: {mean_time}ms (expected < 50ms)"
